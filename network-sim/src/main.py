from pathlib import Path
import pandas as pd
import numpy as np
import fire

from auto_vtt.audio_processing import AudioProcessor
from auto_vtt.speech_to_text import SpeechToTextConverter
from test_runner.model_size_tester import ModelSizeTester
from dataset import VoiceDataset

class Main:
    def evaluate_stt_size(self, root_path: str, model_size: str, max_len: int = None):
        root_path = Path(root_path)
        sizes = {
            "tiny": SpeechToTextConverter.ModelSize.TINY,
            "base": SpeechToTextConverter.ModelSize.BASE,
            "small": SpeechToTextConverter.ModelSize.SMALL,
            "medium": SpeechToTextConverter.ModelSize.MEDIUM,
            "large": SpeechToTextConverter.ModelSize.LARGE,
        }
        
        truth_csv = pd.read_csv(root_path / "data" / "train_data.csv")
        dataset = VoiceDataset(truth_csv=truth_csv, root_dir=root_path, audio_processor=AudioProcessor(), max_len=max_len)
        tester = ModelSizeTester(sizes[model_size], dataset)
        acc = tester.evaluate_model_size()
        
        return acc
    
    
if __name__ == "__main__":
    fire.Fire(Main)