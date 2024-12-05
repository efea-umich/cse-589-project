#!/usr/bin/env python
"""
# MEAN: 458 ms
# ST DEV: 201ms

Measurement topology for EECS489, Winter 2024, Assignment 1
"""
meanDelay = 458
stdDevDelay = 201
numLinks = 4
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.link import TCIntf
from mininet.topo import Topo
from mininet.log import setLogLevel

import random
import threading
import time

# Combination of autogregressive function and 
def genDelayValue():
    # TODO: Change latency generation
    return meanDelay

class AssignmentNetworks(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        # Move host by creating and deleting links and nodes from network
        # Square on outside where host may move, Internal 2 switches that connect all nodes

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')

        s1 = self.addSwitch('s1')
        s2 = self.addSwithc('s2')


        meanDelayVal = str(meanDelay) + 'ms'
        self.addLink(h1, s1, delay = meanDelayVal)
        self.addLink(h2, s1, delay = meanDelayVal)
        self.addLink(h3, s2, delay = meanDelayVal)
        self.addLink(h4, s2, delay = meanDelayVal)
        self.addLink(s1, s2, delay = meanDelayVal)


def update_link_delays(net, mean=meanDelay, stddev=stdDevDelay):
    """Function to update link delays using a normal distribution."""
    while True:
        for link in net.links:
            # Generate a random delay based on normal distribution
            delay = abs(random.gauss(mean, stddev))  # Ensure delay is non-negative
            # delay = genDelayValue()
            delay_str = f'{delay:.2f}ms'
            intf1, intf2 = link.intf1, link.intf2
            print(f"Updating delay on link {intf1} - {intf2} to {delay_str}")

            # Apply the delay to both interfaces
            intf1.config(delay=delay_str)
            intf2.config(delay=delay_str)

        # Wait for 10 seconds before updating delays again
        time.sleep(10)


def call_host_function(host, function_name, *args):
    """Call a function on a specific host."""
    # Sample Function
    if function_name == "ping":
        print(f"{host.name} is pinging {args[0]}")
        host.cmd(f'ping -c 4 {args[0]}')
    

def main():
    setLogLevel( 'info' )

    # Create data network
    topo = AssignmentNetworks()
    net = Mininet(topo=topo, link=TCLink, autoSetMacs=True,
           autoStaticArp=True)
    
    net.start()

    # Start the delay update thread
    delay_thread = threading.Thread(target=update_link_delays, args=(net,))
    delay_thread.daemon = True  # Daemon thread will stop with the main program
    delay_thread.start()

    
    h1 = net.get('h1')
    h2 = net.get('h2')

    # h2.IP() appears in mininet docs but does not seem to work
    call_host_function(h1, "ping", "10.0.0.2")



    # Run network
    
    CLI( net )
    net.stop()