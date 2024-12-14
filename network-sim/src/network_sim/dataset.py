from typing import Optional
import pandas as pd
import numpy as np

from pathlib import Path
from torch.utils.data import Dataset
from pydub import AudioSegment
from loguru import logger

from auto_vtt.audio_processing import AudioProcessor
from tqdm import tqdm


class VoiceDataset(Dataset):
    def __init__(
        self,
        root_dir: Path,
        audio_processor: AudioProcessor,
        max_len: Optional[int] = None,
    ):
        self.truth_csv = pd.read_csv(root_dir / "data" / "train_data.csv")
        self.truth_csv = self.truth_csv[
            (self.truth_csv["action"] != "none") & (self.truth_csv["object"] != "none")
        ]
        if max_len is not None:
            self.truth_csv = self.truth_csv.head(max_len)

        self.root_dir = root_dir
        self.audio_processor = audio_processor

        self.data = []
        self.init_data()

    def init_data(self):
        logger.info("Initializing data")
        for row in tqdm(self.truth_csv.itertuples()):
            audio_path = self.root_dir / row.path
            audios = self.audio_processor.process_file(audio_path)
            for type, audio in audios.items():
                action = row.action
                object = row.object
                
                data = {
                    "label": f"{action}:{object}",
                    "transcription": row.transcription
                }
                self.data.append((audio, data))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]
