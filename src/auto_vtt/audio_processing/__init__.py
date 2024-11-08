from pydub import AudioSegment
import numpy as np


class AudioProcessor:
    def process_file(self, audio_file_path) -> AudioSegment:
        """
        Processes the input audio file to simulate the acoustic environment of a moving car.

        Parameters:
        - audio_file_path (str): Path to the input audio file.

        Returns:
        - AudioSegment: The transformed audio segment.
        """
        # Load the original audio file
        try:
            original_audio = AudioSegment.from_file(audio_file_path)
        except Exception as e:
            raise ValueError(f"Could not load audio file: {e}")

        # Generate background noise to simulate car interior noise
        duration_ms = len(original_audio)
        sample_rate = original_audio.frame_rate  # Use the original audio's sample rate
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
            channels=1
        )

        # Adjust the volume of the noise and apply a low-pass filter to simulate engine noise
        noise_audio = noise_audio - 30  # Reduce noise volume by 30 dB
        noise_audio = noise_audio.low_pass_filter(1000)  # Low-pass filter at 1 kHz

        # Mix the original audio with the background noise
        mixed_audio = original_audio.overlay(noise_audio)

        # Apply a low-pass filter to the mixed audio to simulate the muffled environment
        mixed_audio = mixed_audio.low_pass_filter(8000)  # Low-pass filter at 8 kHz

        # Simulate slight reverb by adding delayed and attenuated copies of the audio
        delay_times = [50, 100, 150]  # Delay times in milliseconds
        decay_factors = [0.5, 0.3, 0.2]  # Corresponding decay factors for each delay

        for delay, decay in zip(delay_times, decay_factors):
            # Create a delayed and attenuated version of the mixed audio
            delayed_audio = (mixed_audio - (10 * decay))
            delayed_audio = AudioSegment.silent(duration=delay) + delayed_audio
            delayed_audio = delayed_audio[:len(mixed_audio)]  # Ensure the length matches
            mixed_audio = mixed_audio.overlay(delayed_audio)

        return mixed_audio
