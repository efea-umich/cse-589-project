import numpy as np

from . import LatencyProvider


class DataLatencyProvider(LatencyProvider):
    def __init__(self, data: np.ndarray[float]):
        self.mean = np.mean(data)
        self.std = np.std(data)

    def get_mean_latency(self):
        return self.mean

    def get_std_latency(self):
        return self.std
