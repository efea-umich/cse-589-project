import enum
import whisper
import numpy as np

class SpeechToTextConverter:
    class ModelSize(enum.Enum):
        TINY = 'tiny'
        BASE = 'base'
        SMALL = 'small'
        MEDIUM = 'medium'
        LARGE = 'large'

    def __init__(self, model_size: ModelSize):
        self.model = whisper.load_model(model_size.value)

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes speech from the provided audio file path.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            str: Transcribed text.
        """
        result = self.model.transcribe(audio_path)
        return result['text'].strip()

    def transcribe_array(self, audio_array: np.ndarray, sample_rate: int) -> str:
        """
        Transcribes speech from a NumPy array representing sound.

        Args:
            audio_array (np.ndarray): The audio signal as a NumPy array.
            sample_rate (int): The sample rate of the audio signal.

        Returns:
            str: Transcribed text.
        """
        # Convert the numpy array to the format Whisper expects
        result = self.model.transcribe(audio_array, sample_rate=sample_rate)
        return result['text'].strip()
