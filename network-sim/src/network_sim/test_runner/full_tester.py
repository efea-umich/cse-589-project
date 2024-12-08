import time
from pathlib import Path
from typing import List, Dict
import asyncio

from loguru import logger
import pandas as pd
import numpy as np

from auto_vtt.audio_processing import AudioProcessor
from auto_vtt.speech_to_text import SpeechToTextConverter
from auto_vtt.inferencing.action_classifier import ActionClassifier
from network_sim.latency_provider import LatencyProvider
from network_sim.latency_provider.data_latency_provider import DataLatencyProvider
from network_sim.dataset import VoiceDataset

from network_sim.topology import CSE589Topo
from mininet.net import Mininet
from mininet.node import Controller

import fire

class TestRunner:
    def __init__(self, latency_provider: LatencyProvider, dataset: VoiceDataset, local_model_size: SpeechToTextConverter.ModelSize, remote_model_size: SpeechToTextConverter.ModelSize):
        self.latency_provider = latency_provider
        self.dataset = dataset
        self.local_model_size = local_model_size
        self.remote_model_size = remote_model_size
        self.stt = SpeechToTextConverter(local_model_size)
        self.audio_processor = AudioProcessor()
        
        self.obj_classifier, self.act_classifier = self.get_classifiers(dataset)
        self.topo = CSE589Topo(latency_provider=self.latency_provider)
        
    def get_classifiers(self, dataset: VoiceDataset):
        objects = set()
        actions = set()
        
        for _, label in dataset:
            obj, act = label.split(":")
            objects.add(obj)
            actions.add(act)
            
        obj_classifier = ActionClassifier(objects)
        act_classifier = ActionClassifier(actions)
        
        return obj_classifier, act_classifier
    
class Main:
    def run_test(self, latency_data_path: str, dataset_path: str, local_model_size: str, remote_model_size: str, max_len: int = None):
        latency_data_path = Path(latency_data_path)
        dataset_path = Path(dataset_path)
        
        latency_provider = DataLatencyProvider(pd.read_csv(latency_data_path)['latency'].values)
        dataset = VoiceDataset(
            root_dir=dataset_path,
            audio_processor=AudioProcessor(),
            max_len=max_len
        )
        
        logger.info(f"Local model size: {local_model_size}")
        local_model_size = SpeechToTextConverter.ModelSize(local_model_size)
        remote_model_size = SpeechToTextConverter.ModelSize(remote_model_size)
        
        test_runner = TestRunner(latency_provider, dataset, local_model_size, remote_model_size)
        
        asyncio.run(test_runner.topo.run(60, 1))
        
        results = test_runner.evaluate_model_size()
        print(results)
            
            
if __name__ == "__main__":
    fire.Fire(Main)