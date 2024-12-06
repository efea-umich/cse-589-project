import time
import asyncio
import subprocess
from pathlib import Path
from typing import List
import numpy as np

BITRATE_PROFILES = [
    {"bitrate": 64000, "dir": "bitrate_64"},   # ~64 kbps
    {"bitrate": 128000, "dir": "bitrate_128"}, # ~128 kbps
    {"bitrate": 256000, "dir": "bitrate_256"}  # ~256 kbps
]

class VariableRateStreamer:
    def __init__(self, net, latency_provider, num_segments=5, server_port=8080):
        """
        :param net: The Mininet network instance.
        :param latency_provider: LatencyProvider instance for getting next latency values.
        :param num_segments: Number of segments to stream.
        :param server_port: The port on which the server serves files.
        """
        self.net = net
        self.latency_provider = latency_provider
        self.num_segments = num_segments
        self.server_port = server_port

        self.server = net.get('server')
        self.car = net.get('car')

        # Start from the middle profile
        self.current_profile_index = 1  # 0=low,1=mid,2=high
        self.current_profile = BITRATE_PROFILES[self.current_profile_index]

        # Keep track of throughput measurements (bits/sec)
        self.throughputs = []
        # Keep track of latencies (ms)
        self.latencies = []

    def start_server(self):
        # Start a simple HTTP server on the server host
        # We'll assume we have the directories `bitrate_64`, `bitrate_128`, `bitrate_256`
        # in the server's home directory.
        # Run in background (&). If already running, you might need to kill or skip this.
        self.server.cmd(f'pkill -f "python3 -m http.server {self.server_port}"')
        self.server.cmd(f'python3 -m http.server {self.server_port} &')
        time.sleep(1)  # give the server a moment to start

    def stop_server(self):
        self.server.cmd(f'pkill -f "python3 -m http.server {self.server_port}"')

    def measure_latency(self):
        # Measure latency by using ping once and parsing the result
        # Pinging the server from the car
        output = self.car.cmd(f'ping -c 1 {self.server.IP()}')
        # Usually output contains a line like: "rtt min/avg/max/mdev = 0.063/0.063/0.063/0.000 ms"
        # We'll parse avg latency:
        # If ping fails for some reason, default to a large latency value.
        try:
            line = [l for l in output.split('\n') if 'rtt min/avg/max' in l][0]
            avg = line.split('=')[1].split('/')[1].strip()
            return float(avg)
        except:
            return 1000.0  # default large latency if something goes wrong

    def download_segment(self, segment_index):
        # Download the selected segment at current profile
        profile = self.current_profile
        segment_name = f"segment_{segment_index}.ts"
        url = f"http://{self.server.IP()}:{self.server_port}/{profile['dir']}/{segment_name}"

        # Measure start time
        start = time.time()
        # Download to /dev/null to just measure speed
        output = self.car.cmd(f'curl -o /dev/null -s -w "%{{size_download}} %{{time_total}}" {url}')
        end = time.time()

        # output should contain two values: size_download, time_total
        # Example: "123456 1.234"
        # If curl fails, handle gracefully
        try:
            parts = output.strip().split()
            size_download = int(parts[0])  # bytes
            time_total = float(parts[1])   # seconds
        except:
            # fallback if parsing fails
            size_download = 0
            time_total = end - start

        return size_download, time_total

    def update_profile(self, avg_latency, throughput_bps):
        # Heuristic:
        # Let required_bitrate = current_profile['bitrate']
        # If throughput_bps < required_bitrate * 1.2 or latency > 500ms => consider lowering profile
        # If throughput_bps > required_bitrate * 1.8 and latency < 300ms => consider raising profile
        # Else stay the same
        required_bitrate = self.current_profile['bitrate']

        if (throughput_bps < required_bitrate * 1.2 or avg_latency > 500) and self.current_profile_index > 0:
            self.current_profile_index -= 1
        elif (throughput_bps > required_bitrate * 1.8 and avg_latency < 300) and self.current_profile_index < len(BITRATE_PROFILES) - 1:
            self.current_profile_index += 1

        self.current_profile = BITRATE_PROFILES[self.current_profile_index]

    async def run(self, duration=60, tick_interval=5):
        # Start the server
        self.start_server()

        # Simulate adjusting network latency over time (if latency_provider is used)
        start_time = time.time()

        async def update_latency():
            while time.time() - start_time < duration:
                await asyncio.sleep(tick_interval)
                if self.latency_provider.has_next():
                    latency = self.latency_provider.get_next_latency()
                    # Adjusting topology latency
                    topo = self.net.topo
                    topo.adjust_latency(f"{latency}ms")

        latency_task = asyncio.create_task(update_latency())

        # Stream segments
        for i in range(self.num_segments):
            # Measure latency before downloading the segment
            avg_latency = self.measure_latency()
            self.latencies.append(avg_latency)

            size_download, time_total = self.download_segment(i)
            if time_total == 0:
                time_total = 0.001  # avoid division by zero in case of error

            # Calculate throughput in bits/s (size_download is bytes)
            throughput_bps = (size_download * 8) / time_total
            self.throughputs.append(throughput_bps)

            print(f"Segment {i}: downloaded {size_download} bytes in {time_total:.2f}s, "
                  f"throughput={throughput_bps/1000:.2f} kbps, latency={avg_latency:.2f}ms, "
                  f"profile={self.current_profile['bitrate']} bps")

            # Update profile based on heuristic
            self.update_profile(avg_latency, throughput_bps)

        # Stop the server and latency task
        await latency_task
        self.stop_server()
