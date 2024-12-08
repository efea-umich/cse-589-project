import asyncio
import websockets
from pathlib import Path
import os
import json
from datetime import datetime
import fire

class VariableRateStreamerServer:
    def __init__(self, output_dir: Path, host="localhost", port=8765):
        """
        :param output_dir: Directory where received chunks will be saved.
        :param host: Hostname to bind the server.
        :param port: Port to bind the server.
        """
        output_dir = Path(output_dir)
        self.output_dir = output_dir
        self.host = host
        self.port = port

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

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
                    control_data = json.loads(message)
                    if control_data.get("event") == "done":
                        print("Client finished streaming.")
                        break
                else:
                    # Save the received chunk
                    chunk_file = self.output_dir / f"chunk_{chunk_idx:04d}.wav"
                    with open(chunk_file, "wb") as f:
                        f.write(message)

                    print(f"Received chunk {chunk_idx} ({len(message)} bytes)")
                    chunk_idx += 1

            except websockets.ConnectionClosed as e:
                print(f"Client disconnected: {e}")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

        print("Connection closed.")

    async def start(self):
        """
        Start the WebSocket server.
        """
        print(f"Starting server at ws://{self.host}:{self.port}")
        start_server = await websockets.serve(self.handler, self.host, self.port)
        await start_server.serve_forever()


if __name__ == "__main__":
    fire.Fire(VariableRateStreamerServer)