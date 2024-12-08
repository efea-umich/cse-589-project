import asyncio
import websockets
import json
import time
from pathlib import Path
from subprocess import PIPE
import statistics
import fire


class VariableRateStreamerClient:
    def __init__(
        self,
        original_file_path: Path,
        server_uri: str,
        chunk_size: int = 4096,
        initial_bitrate: int = 128000,
        encoding_params: dict = None,
        adaptation_interval: int = 10  # Only adapt every N chunks
    ):
        self.original_file_path = original_file_path
        self.server_uri = server_uri
        self.chunk_size = chunk_size
        self.current_bitrate = initial_bitrate

        self.rtts = []
        self.throughputs = []
        self.min_bitrate = 64000
        self.max_bitrate = 320000
        self.bitrate_step = 32000

        self.encoding_params = encoding_params or {
            "audio_codec": "libmp3lame",
            "b:a": str(self.current_bitrate),
            "ar": "44100",
            "ac": "2",
            "format": "mp3",
        }

        self.encoder = None
        self.encoder_queue = asyncio.Queue()
        self.encoder_task = None
        self.encoder_lock = asyncio.Lock()  # Prevent simultaneous access
        self.chunk_count = 0
        self.adaptation_interval = adaptation_interval
        self.pending_bitrate_change = False

    async def start_encoder(self):
        """
        Start the ffmpeg encoder as a subprocess.
        """
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(self.original_file_path),
            "-f",
            "mp3",
            "-codec:a",
            self.encoding_params["audio_codec"],
            "-b:a",
            self.encoding_params["b:a"],
            "-ar",
            self.encoding_params["ar"],
            "-ac",
            self.encoding_params["ac"],
            "pipe:1",
        ]

        self.encoder = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.encoder_task = asyncio.create_task(self.read_encoder_output())

    async def read_encoder_output(self):
        """
        Read chunks from the encoder and put them into the queue.
        """
        try:
            while True:
                chunk = await self.encoder.stdout.read(self.chunk_size)
                if not chunk:
                    break
                await self.encoder_queue.put(chunk)
        except asyncio.CancelledError:
            pass

    async def restart_encoder(self):
        """
        Gracefully restart the encoder with updated parameters.
        """
        async with self.encoder_lock:
            # Terminate existing encoder
            if self.encoder:
                self.encoder.terminate()
                await self.encoder.wait()
                self.encoder_task.cancel()
                try:
                    await self.encoder_task
                except asyncio.CancelledError:
                    pass

            # Clear any stale chunks in the queue
            while not self.encoder_queue.empty():
                self.encoder_queue.get_nowait()

            # Update bitrate and restart
            self.encoding_params["b:a"] = str(self.current_bitrate)
            await self.start_encoder()

    def update_profile(self, avg_rtt, measured_throughput):
        """
        Update the bitrate based on RTT and throughput, but only restart if it actually changed.
        """
        old_bitrate = self.current_bitrate

        # Throughput-based adaptation
        if measured_throughput < self.current_bitrate * 0.8:
            self.current_bitrate = max(self.min_bitrate, self.current_bitrate - self.bitrate_step)
        elif measured_throughput > self.current_bitrate * 1.2:
            self.current_bitrate = min(self.max_bitrate, self.current_bitrate + self.bitrate_step)

        # RTT-based adaptation
        if avg_rtt > 0.2:
            self.current_bitrate = max(self.min_bitrate, self.current_bitrate - self.bitrate_step)

        if self.current_bitrate != old_bitrate:
            # Mark that we need to restart encoder after a short delay
            self.pending_bitrate_change = True

    async def measure_rtt(self, websocket):
        """
        Measure RTT using WebSocket pings.
        """
        start = time.perf_counter()
        pong_waiter = await websocket.ping()
        await pong_waiter
        end = time.perf_counter()
        return end - start

    async def stream_file(self, websocket):
        """
        Stream MP3-encoded data in byte-sized chunks.
        """
        # for now, just send the entire file
        with open(self.original_file_path, "rb") as f:
            bytes = f.read()
        await websocket.send(bytes)
        await websocket.send(json.dumps({"event": "done"}))

    async def run(self):
        """
        Run the streaming client.
        """
        await self.start_encoder()
        async with websockets.connect(self.server_uri) as websocket:
            print(f"Connected to {self.server_uri}")
            await self.stream_file(websocket)

    def __del__(self):
        if self.encoder and self.encoder.returncode is None:
            self.encoder.kill()


if __name__ == "__main__":
    fire.Fire(VariableRateStreamerClient)
