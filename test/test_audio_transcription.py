import pytest

from auto_vtt.speech_to_text import SpeechToTextConverter

def test_audio_transcription():
    converter = SpeechToTextConverter(SpeechToTextConverter.ModelSize.TINY)
    audio_path = 'test/resources/test_audio.wav'
    transcription = converter.transcribe(audio_path)
    assert transcription == "Activate basement lights."