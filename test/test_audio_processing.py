import pytest
from pathlib import Path

from auto_vtt.audio_processing import AudioProcessor

resource_path = Path('test/resources')
output_path = Path('test/resources/tmp')

def test_car_audio_processing():
    processor = AudioProcessor()
    audio_path = resource_path / 'test_audio.wav'

    processed_audio = processor.process_file(audio_path)
    processed_audio.export(output_path / 'processed_audio.wav', format='wav')

    assert True

if __name__ == '__main__':
    pytest.main()