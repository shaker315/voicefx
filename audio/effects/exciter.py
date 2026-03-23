import numpy as np

from .base import BaseEffect


class ExciterEffect(BaseEffect):
    def __init__(self):
        self.hp = 0.0
        self.prev_x = 0.0
        self.alpha = 0.82

    def process(self, signal, state):
        if not state.exciter_on or not state.fx_master_on:
            return signal

        amount = max(1.0, min(10.0, float(state.exciter)))
        drive = 1.2 + ((amount - 1.0) / 9.0) * 3.0
        mix = 0.08 + ((amount - 1.0) / 9.0) * 0.22

        hp = np.empty_like(signal)
        for i, x in enumerate(signal):
            self.hp = self.alpha * (self.hp + x - self.prev_x)
            self.prev_x = x
            hp[i] = self.hp

        excited = np.tanh(hp * drive) * 0.6
        return signal + excited * mix
