import csv
from pathlib import Path
import jiwer
import fire

from collections import defaultdict

from loguru import logger
import numpy as np
from tqdm import tqdm
from network_sim.dataset import VoiceDataset
from sklearn.metrics import accuracy_score

from whisper.normalizers import EnglishTextNormalizer
from auto_vtt.audio_processing import AudioProcessor
from auto_vtt.speech_to_text import SpeechToTextConverter


class ModelSizeTester:
    def __init__(
        self, model_size: SpeechToTextConverter.ModelSize, dataset: VoiceDataset
    ):
        self.model_size = model_size
        self.dataset = dataset
        self.stt = SpeechToTextConverter(model_size)

    def evaluate_model_size(self):
        results = []
        normalize = EnglishTextNormalizer()
        i = 0
        transcript_file = open(f"transcripts_{self.model_size}.txt", "w")
        csv_writer = csv.writer(transcript_file)
        csv_writer.writerow(["transcription", "truth", "label"])
        for audio, data in tqdm(self.dataset):
            transcription = data["transcription"]
            label = data["label"]
            text = self.stt.transcribe(audio)
            csv_writer.writerow([text, transcription, label])
            i += 1
            results.append(
                jiwer.wer(normalize(transcription), normalize(text))
            )
            
        transcript_file.close()

        results = np.mean(results)
        return results


def main(dataset_root: str, model_size: str, max_len: int):
    dataset_root = Path(dataset_root)
    dataset = VoiceDataset(dataset_root, AudioProcessor(), max_len)
    tester = ModelSizeTester(SpeechToTextConverter.ModelSize(model_size), dataset)
    results = tester.evaluate_model_size()
    print(results)
    

if __name__ == "__main__":
    fire.Fire(main)