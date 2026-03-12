import numpy as np
from .base import BaseEffect


class SoftLimiterEffect(BaseEffect):
    def process(self, signal, state):
        threshold = 0.9
        return np.tanh(signal / threshold) * threshold