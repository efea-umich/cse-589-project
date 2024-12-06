import time
from pathlib import Path
from typing import Optional

from mininet.net import Mininet
from mininet.node import Controller, Host
from mininet.link import TCLink, Link
from mininet.topo import Topo

from latency_provider import LatencyProvider

import asyncio


class CSE589Topo(Topo):
    def __init__(self, latency_provider: LatencyProvider):
        Topo.__init__(self)

        self.latency_provider = latency_provider

        self.car = self.addHost('car')
        self.server = self.addHost('server')

        self.link = self.addLink(self.car, self.server, cls=TCLink, bw=10, delay='10ms', loss=0)


    def adjust_latency(self, latency: str):
        self.link.intf1.config(delay=latency)
        self.link.intf2.config(delay=latency)

    async def run(self, duration: int, tick_interval: int):
        net = Mininet(topo=self, controller=Controller)
        start_time = time.time()
        net.start()

        while time.time() - start_time < duration:
            await asyncio.sleep(tick_interval)
            latency = self.latency_provider.get_next_latency()
            self.adjust_latency(f"{latency}ms")
        net.stop()
