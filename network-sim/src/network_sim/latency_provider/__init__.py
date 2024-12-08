from abc import ABC, abstractmethod


class LatencyProvider(ABC):
    @abstractmethod
    def get_mean_latency(self) -> float:
        pass

    @abstractmethod
    def get_std_latency(self) -> float:
        pass
