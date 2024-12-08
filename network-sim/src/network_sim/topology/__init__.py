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
    def __init__(self, latency_provider: LatencyProvider):
        Topo.__init__(self)

        self.latency_provider = latency_provider

        self.car = self.addHost("car")
        self.server = self.addHost("server")

        self.link = self.addLink(self.car, self.server, cls=TCLink)

        self.net = Mininet(topo=self, controller=OVSController)
        self.net.start()

        link = self.net.links[0]
        
        logger.info(f"Setting latency to {self.latency_provider.get_mean_latency() / 2}ms with jitter {self.latency_provider.get_std_latency() / 2}ms", bw="100m")
        
        link.intf1.config(
            delay=f"{self.latency_provider.get_mean_latency() / 2}ms",
            jitter=f"{self.latency_provider.get_std_latency() / 2}ms",
            bw=100
        )
        link.intf2.config(
            delay=f"{self.latency_provider.get_mean_latency() / 2}ms",
            jitter=f"{self.latency_provider.get_std_latency() / 2}ms",
            bw=100
        )

    def __del__(self):
        self.net.stop()
