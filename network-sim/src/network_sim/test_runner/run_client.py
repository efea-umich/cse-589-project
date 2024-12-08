from pathlib import Path
import sys
import time
import fire

from loguru import logger
from auto_vtt.streaming.client import VariableRateStreamerClient

logger.remove()
logger.add(sys.stdout)

async def main(server_ip: str, input_dir: str):
    input_dir = Path(input_dir)

    client = VariableRateStreamerClient(
        server_uri=f"ws://{server_ip}:8765"
    )
    with open(input_dir / "example.wav", "rb") as f:
        data = f.read()
    async with client:
        start_time = time.time()
        await client.stream_file(data)
        done_time = time.time()
    
    logger.info(f"Time taken: {done_time - start_time:.2f}s")


if __name__ == "__main__":
    fire.Fire(main)
