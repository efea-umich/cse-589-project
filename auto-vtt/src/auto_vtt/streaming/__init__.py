import time
from pathlib import Path
from typing import List, Dict
import asyncio

from src.auto_vtt.audio_processing import AudioProcessor
from src.auto_vtt.speech_to_text import SpeechToTextConverter
from src.auto_vtt.inferencing.action_classifier import ActionClassifier
from mininet.net import Mininet
from mininet.node import Controller


class TestRunner:
    def __init__(self, latency_provider, audio_files: List[Path], ground_truth: Dict[Path, str],
                 model_sizes: List[SpeechToTextConverter.ModelSize], noise_levels: List[float],
                 remote_inference_enabled: bool, lambda_penalty: float = 0.001):
        self.latency_provider = latency_provider
        self.audio_files = audio_files
        self.ground_truth = ground_truth
        self.model_sizes = model_sizes
        self.noise_levels = noise_levels
        self.remote_inference_enabled = remote_inference_enabled
        self.lambda_penalty = lambda_penalty

        self.audio_processor = AudioProcessor()
        self.local_classifier = ActionClassifier(['music', 'navigation', 'news'])  # example
        self.local_actions = ActionClassifier(['play', 'stop', 'skip'])  # example

    def local_inference(self, text: str):
        start = time.time()
        obj_label, _ = self.local_classifier(text)
        action_label, _ = self.local_actions(text)
        end = time.time()
        return f"{action_label}:{obj_label}", (end - start) * 1000  # ms

    def remote_inference(self, text: str):
        # Placeholder for a remote inference call
        # This might involve making an OpenAI API call or calling a function stub.
        # For simplicity, assume similar latency and result:
        start = time.time()
        # ... perform remote call
        # In actual code, you'd call out to GPT-4o model as shown in the test code.
        end = time.time()
        return "play:music", (end - start) * 1000  # ms, dummy result

    def process_and_transcribe_audio(self, audio_path: Path, model_size: SpeechToTextConverter.ModelSize,
                                     noise_level: float):
        # Process audio
        processed = self.audio_processor.process_file(audio_path, noise_level=noise_level)
        # Assume we pick a certain processed output, e.g. 'turnsignal'
        chosen_noise = 'turnsignal'
        processed_audio = processed[chosen_noise]
        processed_audio_path = Path('tmp_audio.wav')
        processed_audio.export(processed_audio_path, format='wav')

        # Transcribe
        converter = SpeechToTextConverter(model_size)
        start = time.time()
        transcription = converter.transcribe(processed_audio_path)
        end = time.time()
        stt_latency = (end - start) * 1000  # ms
        return transcription, stt_latency

    async def run_tests(self, duration: int = 60, tick_interval: int = 5):
        topo = CSE589Topo(latency_provider=self.latency_provider)
        net = Mininet(topo=topo, controller=Controller)
        net.start()

        # Start latency updates
        async def update_latency():
            start_time = time.time()
            while time.time() - start_time < duration:
                await asyncio.sleep(tick_interval)
                if self.latency_provider.has_next():
                    latency = self.latency_provider.get_next_latency()
                    topo.adjust_latency(f"{latency}ms")

        latency_task = asyncio.create_task(update_latency())

        results = []
        for audio_file in self.audio_files:
            truth = self.ground_truth[audio_file]
            for model_size in self.model_sizes:
                for noise_level in self.noise_levels:
                    # Simulate processing and STT
                    transcription, stt_latency = self.process_and_transcribe_audio(audio_file, model_size, noise_level)

                    # Perform inference
                    if self.remote_inference_enabled:
                        inferred, inf_latency = self.remote_inference(transcription)
                    else:
                        inferred, inf_latency = self.local_inference(transcription)

                    # Compute accuracy for this one sample
                    # Here assume truth and inferred strings can be compared directly
                    accuracy = 1.0 if truth == inferred else 0.0

                    total_latency = stt_latency + inf_latency
                    qoe = accuracy * (2.71828 ** (-self.lambda_penalty * total_latency))  # e^{-\lambda t}

                    results.append({
                        "audio_file": str(audio_file),
                        "model_size": model_size.name,
                        "noise_level": noise_level,
                        "inference_mode": "remote" if self.remote_inference_enabled else "local",
                        "transcription": transcription,
                        "inferred": inferred,
                        "accuracy": accuracy,
                        "total_latency_ms": total_latency,
                        "qoe": qoe
                    })

        # Stop latency simulation and network
        await latency_task
        net.stop()

        return results

# Example usage:
# latency_provider = DataLatencyProvider(np.loadtxt("latencies.csv"))
# runner = TestRunner(latency_provider, [Path("command1.wav"), Path("command2.wav")],
#                     {"command1.wav": "play:music", "command2.wav": "navigation:somewhere"},
#                     [SpeechToTextConverter.ModelSize.TINY, SpeechToTextConverter.ModelSize.SMALL],
#                     [0.1, 0.5],
#                     remote_inference_enabled=False)

# results = asyncio.run(runner.run_tests())
# for r in results:
#     print(r)
