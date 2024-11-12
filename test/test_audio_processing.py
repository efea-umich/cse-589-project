# run with: PYTHONPATH=src pytest test/test_audio_processing.py

import pytest
from pathlib import Path

from src.auto_vtt.audio_processing import AudioProcessor

resource_path = Path("test/resources")
output_path = Path('test/resources/tmp')

def test_car_audio_processing():
    processor = AudioProcessor()
    audio_path = resource_path / 'test_audio.wav'

    processed_audio_results = processor.process_file(audio_path)
    for noisetype, result in processed_audio_results.items():
        filename = f"processed_audio_{noisetype}.wav"
        result.export(output_path / filename, format='wav')

    assert True

if __name__ == '__main__':
    pytest.main()
