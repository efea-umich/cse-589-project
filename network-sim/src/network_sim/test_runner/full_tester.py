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

import network_sim
from network_sim.topology import CSE589Topo
from mininet.net import Mininet
from mininet.node import Controller

import fire


class TestRunner:
    def __init__(
        self,
        latency_provider: LatencyProvider,
        dataset: VoiceDataset,
        local_model_size: SpeechToTextConverter.ModelSize,
        remote_model_size: SpeechToTextConverter.ModelSize,
        output_dir: str,
        input_dir: str,
    ):
        self.output_dir = Path(output_dir)
        self.input_dir = Path(input_dir)

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

    async def run_mn_command_in_thread(self, host: str, command: str):
        host = self.topo.net.getNodeByName(host)
        p = host.popen(command.split())
        while p.poll() is None:
            await asyncio.sleep(0.1)

        output, err = p.communicate()
        if err:
            logger.error(err)
            raise Exception(err)
        return output

    async def evaluate(self):
        server_node = self.topo.net.getNodeByName("server")
        client_node = self.topo.net.getNodeByName("car")
        server_ip = server_node.IP()
        
        runner_path = Path(__file__).parent 
        
        server_runner_path = runner_path / "run_server.py"
        client_runner_path = runner_path / "run_client.py"

        server_process = server_node.popen(
            f"uv run {server_runner_path} --output_dir {self.output_dir}"
        )

        for audio_file, label in self.dataset:
            audio_file.export(self.input_dir / "example.wav", format="wav")

            client_process = client_node.popen(
                f"uv run {client_runner_path} --server-ip {server_ip} --input_dir {self.input_dir}"
            )
            # wait for client to finish
            while client_process.poll() is None:
                await asyncio.sleep(0.1)

            client_output, client_err = client_process.communicate()
            if client_err:
                logger.error(client_err)
            logger.info(client_output)

class Main:
    async def run_test(
        self,
        latency_data_path: str,
        dataset_path: str,
        local_model_size: str,
        remote_model_size: str,
        max_len: int = None,
        output_dir: str = "output",
        input_dir: str = "input",
    ):
        latency_data_path = Path(latency_data_path)
        dataset_path = Path(dataset_path)

        latency_provider = DataLatencyProvider(
            pd.read_csv(latency_data_path)["latency"].values
        )
        dataset = VoiceDataset(
            root_dir=dataset_path, audio_processor=AudioProcessor(), max_len=max_len
        )

        local_model_size = SpeechToTextConverter.ModelSize(local_model_size)
        remote_model_size = SpeechToTextConverter.ModelSize(remote_model_size)

        test_runner = TestRunner(
            latency_provider,
            dataset,
            local_model_size,
            remote_model_size,
            output_dir,
            input_dir,
        )

        results = await test_runner.evaluate()


if __name__ == "__main__":
    fire.Fire(Main)
