import asyncio
import time
import websockets

BITRATE_PROFILES = [
    {"bitrate": 64000, "file": "audio_64kbps.bin"},
    {"bitrate": 128000, "file": "audio_128kbps.bin"},
    {"bitrate": 256000, "file": "audio_256kbps.bin"}
]

CHUNK_SIZE = 1024

class VariableRateStreamerClient:
    def __init__(self, server_uri):
        self.server_uri = server_uri
        self.current_profile_index = 1
        self.current_profile = BITRATE_PROFILES[self.current_profile_index]
        self.rtts = []
        self.throughputs = []

    def update_profile(self, avg_rtt, measured_throughput):
        current_bitrate = self.current_profile['bitrate']
        if avg_rtt > 0.5 or measured_throughput < current_bitrate * 1.2:
            if self.current_profile_index > 0:
                self.current_profile_index -= 1
        elif avg_rtt < 0.3 and measured_throughput > current_bitrate * 1.8:
            if self.current_profile_index < len(BITRATE_PROFILES)-1:
                self.current_profile_index += 1
        self.current_profile = BITRATE_PROFILES[self.current_profile_index]

    async def stream_file(self, websocket):
        with open(self.current_profile['file'], 'rb') as f:
            data = f.read()

        total_sent = 0
        start_time = time.time()
        MIN_RTT_SAMPLES = 5

        while total_sent < len(data):
            chunk = data[total_sent:total_sent+CHUNK_SIZE]
            send_time = time.time()
            await websocket.send(chunk)

            ack_line = await websocket.recv()  # Wait for ACK
            recv_time = time.time()
            parts = ack_line.split()
            if len(parts) == 3 and parts[0] == "ACK":
                rtt = recv_time - send_time
                self.rtts.append(rtt)
                chunk_bits = len(chunk)*8
                throughput = chunk_bits / rtt
                self.throughputs.append(throughput)

                if len(self.rtts) >= MIN_RTT_SAMPLES:
                    avg_rtt = sum(self.rtts) / len(self.rtts)
                    avg_thr = sum(self.throughputs) / len(self.throughputs)
                    self.update_profile(avg_rtt, avg_thr)
                    print(f"Adaptation: avg RTT={avg_rtt*1000:.2f}ms, avg_thr={avg_thr/1000:.2f}kbps, profile={self.current_profile['bitrate']} bps")

            total_sent += len(chunk)

        total_time = time.time() - start_time
        print(f"Finished streaming {len(data)} bytes in {total_time:.2f}s")

    async def run(self):
        async with websockets.connect(self.server_uri) as websocket:
            print(f"Connected to {self.server_uri}")
            await self.stream_file(websocket)

if __name__ == "__main__":
    server_uri = "ws://10.0.0.2:9999"  # Replace with your server's address
    client = VariableRateStreamerClient(server_uri)
    asyncio.run(client.run())
