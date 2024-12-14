import sys
import fire

from loguru import logger
from auto_vtt.streaming.server import VariableRateStreamerServer

logger.remove()
logger.add(sys.stdout)

def on_done_processing():
    logger.info("Processing done.")

async def main(output_dir: str):
    server = VariableRateStreamerServer(output_dir, on_done_processing, port=8765)
    await server.start()


if __name__ == "__main__":
    fire.Fire(main)
