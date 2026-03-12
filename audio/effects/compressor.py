import numpy as np
from .base import BaseEffect


class CompressorEffect(BaseEffect):
    def process(self, signal, state):

        signal = signal.copy()

        threshold = state.compressor_threshold
        ratio = state.compressor_ratio

        over = np.abs(signal) > threshold

        signal[over] = np.sign(signal[over]) * (
            threshold + (np.abs(signal[over]) - threshold) / ratio
        )

        return signal