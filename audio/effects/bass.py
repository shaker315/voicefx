import numpy as np
from .base import BaseEffect


class BassBoostEffect(BaseEffect):
    def __init__(self, samplerate=48000, cutoff=120.0):
        self.low1 = 0.0
        self.low2 = 0.0
        self.cutoff = cutoff
        self.samplerate = samplerate
        self.alpha = (2 * np.pi * cutoff) / (2 * np.pi * cutoff + samplerate)

    def process(self, signal, state):

        if signal is None:
            return signal

        if not state.bass_on or not state.fx_master_on:
            return signal

        low = np.zeros_like(signal)

        for i in range(len(signal)):
            self.low1 += self.alpha * (signal[i] - self.low1)
            self.low2 += self.alpha * (self.low1 - self.low2)
            low[i] = self.low2

        return signal + low * (state.bass_gain - 1.0)
