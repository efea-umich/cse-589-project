from pydub import AudioSegment
import numpy as np
from pathlib import Path

from loguru import logger


class AudioProcessor:
    def __init__(self):
        noise_path = Path(__file__).parent / "car_sounds"
        car_noise_paths = {
            "ac": noise_path / "car_ac.flac",
            "convo": noise_path / "car_conversation_music.wav",
            "radio": noise_path / "car_radio.wav",
            "turnsignal": noise_path / "car_turnsignal.mp3",
        }
        
        self.car_noises = {}
        
        for noise, file in car_noise_paths.items():
            self.car_noises[noise] = AudioSegment.from_file(file)
    
    def process_file(self, audio_file_path) -> AudioSegment:
        """
                Processes the input audio file to simulate the acoustic environment of a moving car.

                Parameters:
                - audio_file_path (str): Path to the input audio file.
        x
                Returns:
                - AudioSegment: The transformed audio segment.
        """
        # Load the original audio file
        try:
            original_audio = AudioSegment.from_file(audio_file_path)
        except Exception as e:
            raise ValueError(f"Could not load audio file: {e}")

        return self.process_audio(original_audio)

    def process_audio(self, audio: AudioSegment) -> AudioSegment:
        # Generate background noise to simulate car interior noise
        duration_ms = len(audio)
        sample_rate = audio.frame_rate  # Use the original audio's sample rate
        num_samples = int(duration_ms * sample_rate / 1000.0)

        # Generate white noise
        samples = np.random.normal(0, 1, size=num_samples)
        samples /= np.max(np.abs(samples))  # Normalize to -1 to 1

        # Convert numpy array to 16-bit PCM audio segment
        samples_int16 = (samples * 32767).astype(np.int16)
        noise_audio = AudioSegment(
            samples_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16 bits = 2 bytes
            channels=1,
        )

        # Adjust the volume of the noise and apply a low-pass filter to simulate engine noise
        noise_audio = noise_audio - 30  # Reduce noise volume by 30 dB
        # noise_audio = noise_audio.low_pass_filter(1000)  # Low-pass filter at 1 kHz

        # Mix the original audio with the background noise
        mixed_audio = audio.overlay(noise_audio)

        # Apply a low-pass filter to the mixed audio to simulate the muffled environment
        mixed_audio = mixed_audio.low_pass_filter(8000)  # Low-pass filter at 8 kHz

        mixed_with_car_sounds = {"noise": mixed_audio}

        for noise, noise_audio in self.car_noises.items():
            new_segment = audio.overlay(noise_audio).low_pass_filter(
                5000
            )
            mixed_with_car_sounds[noise] = new_segment

        return mixed_with_car_sounds
