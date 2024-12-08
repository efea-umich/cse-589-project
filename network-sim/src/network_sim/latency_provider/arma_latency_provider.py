import numpy as np

from collections import deque
from dataclasses import dataclass

from statsmodels.tsa.arima.model import ARIMA

from . import LatencyProvider


def with_prob(prob):
    return np.random.rand() < prob


@dataclass
class Distribution:
    mean: np.float32
    std: np.float32


class LatencyModel(LatencyProvider):
    def __init__(
        self,
        data: np.ndarray,
        lag: int,
        dist_spike: Distribution,
        spike_prob: float,
    ):
        self.p = lag
        self.q = 0
        self.dist_latency = Distribution(mean=np.mean(data), std=np.std(data))
        self.dist_spike = dist_spike
        self.spike_prob = spike_prob
        self.spike_len_remaining = 0

        self.prev_values = deque(data[-self.p :], maxlen=self.p)
        self.prev_resids = deque([0] * self.q, maxlen=self.q)

        self.fit = ARIMA(data, order=(self.p, 0, self.q)).fit()

    def get_next_arima(self):
        ar_term = np.dot(
            self.fit.arparams, list(self.prev_values)[-len(self.fit.arparams) :]
        )
        ma_term = np.dot(
            self.fit.maparams, list(self.prev_resids)[-len(self.fit.maparams) :]
        )

        noise = np.random.normal(scale=np.sqrt(self.fit.params["sigma2"]))
        next_val = self.fit.params["const"] + ar_term + ma_term + noise

        self.prev_values.append(next_val)
        self.prev_resids.append(noise)

        return next_val

    def get_next_latency(self) -> float:
        return self.get_next_arima()

    def has_next(self) -> bool:
        return True

    def iterator(self, n: int):
        for i in range(n):
            next_val = self.get_next_arima()
            yield next_val
