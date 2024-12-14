import subprocess
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

from tqdm import tqdm

import fire


class TestRunner:
    def __init__(
        self,
        latency_provider: LatencyProvider,
        dataset: VoiceDataset,
        output_dir: str,
        input_dir: str,
    ):
        self.output_dir = Path(output_dir)
        self.input_dir = Path(input_dir)

        self.latency_provider = latency_provider
        self.dataset = dataset
        self.audio_processor = AudioProcessor()

        self.topo = CSE589Topo(latency_mean=latency_provider.get_mean_latency(), latency_std=latency_provider.get_std_latency())


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
            f"uv run {server_runner_path} --output_dir {self.output_dir}",
            stdout=subprocess.PIPE,
        )
        
        # wait for some output from the server
        while True:
            line = server_process.stdout.readline()
            if not line:
                break
            break
        
        logger.info("Server is ready")
        await asyncio.sleep(2)

        for i in tqdm(range(100)):
            audio_file, _ = self.dataset[np.random.randint(len(self.dataset))]
            audio_file.export(self.input_dir / "example.wav", format="wav")
            new_latency = self.latency_provider.get_mean_latency()
            new_jitter = self.latency_provider.get_std_latency()
            self.topo.update_latency(new_latency, new_jitter)

            log_suffix = f"{new_latency}_{new_jitter}_{time.time()}"
            client_process = client_node.popen(
                f"uv run {client_runner_path} --server-ip {server_ip} --input_dir {self.input_dir} --log-suffix {log_suffix}"
            )
            # wait for client to finish
            while client_process.poll() is None:
                await asyncio.sleep(0.1)

            client_output, client_err = client_process.communicate()
            if client_err:
                logger.error(client_err)
            
class ManualLatencyProvider(LatencyProvider):
    def __init__(self, min_latency: float, max_latency: float, min_std_mult: float = 0.5, max_std_mult: float = 1.5):
        self.min_latency = min_latency
        self.max_latency = max_latency
        self.min_std_mult = min_std_mult
        self.max_std_mult = max_std_mult
        
        self.last_latency = self.get_mean_latency()
        
    def get_mean_latency(self) -> float:
        self.last_latency = np.random.uniform(self.min_latency, self.max_latency)
        return self.last_latency

    def get_std_latency(self) -> float:
        return self.last_latency * np.random.uniform(self.min_std_mult, self.max_std_mult)


class Main:
    async def run_test(
        self,
        dataset_path: str,
        latency_mean: tuple,
        latency_std: tuple,
        max_len: int = None,
        output_dir: str = "output",
        input_dir: str = "input",
    ):
        output_dir = Path(output_dir)
        input_dir = Path(input_dir)
        dataset_path = Path(dataset_path)
        
        output_dir.mkdir(exist_ok=True)
        input_dir.mkdir(exist_ok=True)

        latency_provider = ManualLatencyProvider(latency_mean[0], latency_mean[1], latency_std[0], latency_std[1])
        dataset = VoiceDataset(
            root_dir=dataset_path, audio_processor=AudioProcessor(), max_len=max_len
        )

        test_runner = TestRunner(
            latency_provider,
            dataset,
            output_dir,
            input_dir,
        )

        results = await test_runner.evaluate()


if __name__ == "__main__":
    fire.Fire(Main)
