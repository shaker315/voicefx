import numpy as np

from .base import BaseEffect


class BitcrusherEffect(BaseEffect):
    def process(self, signal, state):
        if not state.bitcrusher_on or not state.fx_master_on:
            return signal

        amount = max(1.0, min(10.0, float(state.bitcrusher)))
        hold = int(1 + ((amount - 1.0) / 9.0) * 18)
        bits = int(round(12 - ((amount - 1.0) / 9.0) * 7))
        levels = float(2 ** max(4, bits))

        crushed = np.empty_like(signal)
        held = 0.0
        for i, sample in enumerate(signal):
            if i % hold == 0:
                held = sample
            crushed[i] = held

        crushed = np.round(crushed * levels) / levels
        mix = 0.22 + ((amount - 1.0) / 9.0) * 0.45
        return signal * (1.0 - mix) + crushed * mix
