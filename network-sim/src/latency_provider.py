from abc import ABC, abstractmethod


class LatencyProvider(ABC):

    @abstractmethod
    def has_next(self) -> bool:
        pass

    @abstractmethod
    def get_next_latency(self) -> float:
        pass
