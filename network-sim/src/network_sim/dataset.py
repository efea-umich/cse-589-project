from typing import Optional
import pandas as pd
import numpy as np

from pathlib import Path
from torch.utils.data import Dataset
from pydub import AudioSegment
from loguru import logger

from auto_vtt.audio_processing import AudioProcessor

class VoiceDataset(Dataset):
    def __init__(self, root_dir: Path, audio_processor: AudioProcessor, max_len: Optional[int] = None):
        self.truth_csv = pd.read_csv(root_dir / 'data' / 'train_data.csv')
        self.truth_csv = self.truth_csv[(self.truth_csv["action"] != "none") & (self.truth_csv["object"] != "none")]
        if max_len is not None:
            self.truth_csv = self.truth_csv.head(max_len)
            
        self.root_dir = root_dir
        self.audio_processor = AudioProcessor()
        
    def __len__(self):
        return len(self.truth_csv)
    
    def __getitem__(self, idx):
        audio_path = self.root_dir / self.truth_csv.iloc[idx]['path']
        audio = self.audio_processor.process_file(audio_path)
        
        action = self.truth_csv.iloc[idx]['action']
        object = self.truth_csv.iloc[idx]['object']
        
        return audio, f"{action}:{object}"