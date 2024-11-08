import pytest
from pathlib import Path

from auto_vtt.speech_to_text import SpeechToTextConverter

resource_path = Path('test/resources')

def test_audio_transcription():
    converter = SpeechToTextConverter(SpeechToTextConverter.ModelSize.TINY)
    audio_path = resource_path / 'test_audio.wav'
    transcription = converter.transcribe(audio_path)
    assert transcription == "Activate basement lights."