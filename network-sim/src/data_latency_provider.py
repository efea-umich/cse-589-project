import numpy as np

from latency_provider import LatencyProvider


class DataLatencyProvider(LatencyProvider):
    def __init__(self, data: np.ndarray[float]):
        self.data = data
        self.i = 0

    def get_next_latency(self) -> float:
        latency = self.data[self.i]
        self.i += 1
        return latency

    def has_next(self) -> bool:
        return self.i < len(self.data)