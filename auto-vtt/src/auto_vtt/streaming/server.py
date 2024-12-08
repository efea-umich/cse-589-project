import asyncio
from loguru import logger
import websockets
from pathlib import Path
import os
import json
from datetime import datetime
import fire
from asyncio import Event

class VariableRateStreamerServer:
    def __init__(self, output_dir: Path, on_transmission_finished: callable, host="0.0.0.0", port=8765,):
        """
        :param output_dir: Directory where received chunks will be saved.
        :param host: Hostname to bind the server.
        :param port: Port to bind the server.
        """
        output_dir = Path(output_dir)
        self.output_dir = output_dir
        self.on_transmission_finished = on_transmission_finished
        self.host = host
        self.port = port
        
        os.makedirs(output_dir, exist_ok=True)
        
        
    async def on_done_processing(self, client_websocket):
        await client_websocket.send("done")

    async def handler(self, websocket):
        """
        Handle incoming WebSocket connections.
        """
        chunk_idx = 0
        while True:
            try:
                # Receive a chunk
                message = await websocket.recv()

                # If the message is a control message, process it
                if isinstance(message, str):
                    if message == "done":
                        logger.info("Client finished streaming.")
                        self.on_transmission_finished()
                        await self.on_done_processing(websocket)
                        break
                else:
                    # Save the received chunk
                    chunk_file = self.output_dir / f"chunk_{chunk_idx:04d}.wav"
                    with open(chunk_file, "wb") as f:
                        f.write(message)

                    logger.info(f"Received chunk {chunk_idx} ({len(message)} bytes)")
                    chunk_idx += 1

            except websockets.ConnectionClosed as e:
                logger.info(f"Client disconnected: {e}")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                break

        logger.info("Connection closed.")

    async def start(self):
        """
        Start the WebSocket server.
        """
        logger.info(f"Starting server at ws://{self.host}:{self.port}")
        start_server = await websockets.serve(self.handler, self.host, self.port)
        await start_server.serve_forever()


if __name__ == "__main__":
    fire.Fire(VariableRateStreamerServer)
