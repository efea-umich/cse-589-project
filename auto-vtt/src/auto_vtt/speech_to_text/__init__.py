import enum
import os
import tempfile
from loguru import logger
import torch
import whisper
import numpy as np
import librosa

from pydub import AudioSegment


class SpeechToTextConverter:
    class ModelSize(enum.Enum):
        TINY = "tiny"
        BASE = "base"
        SMALL = "small"
        MEDIUM = "medium"
        LARGE = "large"

    def __init__(self, model_size: ModelSize):
        self.model = whisper.load_model(model_size.value)

    def transcribe_file(self, audio_path: os.PathLike) -> str:
        """
        Transcribes speech from the provided audio file path.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            str: Transcribed text.
        """
        fp16_supported = torch.cuda.is_available()

        result = self.model.transcribe(str(audio_path), fp16=fp16_supported)
        return result["text"].strip()

    def transcribe(self, audio: AudioSegment) -> str:
        """
        Transcribes speech from a NumPy array representing sound.

        Args:
            audio_array (np.ndarray): The audio signal as a NumPy array.
            sample_rate (int): The sample rate of the audio signal.

        Returns:
            str: Transcribed text.
        """
        # write the audio file to a temporary file
        audio_path = tempfile.mktemp(suffix=".wav")
        audio.export(audio_path, format="wav")

        return self.transcribe_file(audio_path)
