from abc import ABC, abstractmethod


class IAudioProcessor(ABC):
    @abstractmethod
    def process(self, audio: np.ndarray) -> np.ndarray:
        pass