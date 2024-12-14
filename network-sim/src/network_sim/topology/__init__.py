import time
from pathlib import Path
from typing import Optional

from loguru import logger
from mininet.net import Mininet
from mininet.node import OVSController, Host
from mininet.link import TCLink, Link
from mininet.topo import Topo

from network_sim.latency_provider import LatencyProvider

import asyncio
from aiorwlock import RWLock

net_config_lock = RWLock()


class CSE589Topo(Topo):
    def __init__(self, latency_mean: Optional[int] = 100, latency_std: Optional[int] = 10):
        Topo.__init__(self)

        self.car = self.addHost("car")
        self.server = self.addHost("server")

        self.link = self.addLink(self.car, self.server, cls=TCLink)

        self.net = Mininet(topo=self, controller=OVSController)
        self.net.start()

        link = self.net.links[0]
        
        logger.info(f"Setting latency to {latency_mean / 2}ms with jitter {latency_std / 2}ms", bw="50m")
        
        self.update_latency(latency_mean, latency_std)
        
    def update_latency(self, latency_mean: int, latency_std: int):
        link = self.net.links[0]
        link.intf1.config(
            delay=f"{latency_mean / 2}ms",
            jitter=f"{latency_std / 2}ms",
            bw=50
        )
        link.intf2.config(
            delay=f"{latency_mean / 2}ms",
            jitter=f"{latency_std / 2}ms",
            bw=50
        )

    def __del__(self):
        self.net.stop()
