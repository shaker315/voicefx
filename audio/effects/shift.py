import numpy as np

from .base import BaseEffect


class ShiftEffect(BaseEffect):
    def process(self, signal, state):
        if not state.shift_on or not state.fx_master_on:
            return signal

        amount = max(1.0, min(10.0, float(state.shift)))
        factor = 1.0 - ((amount - 1.0) / 9.0) * 0.14

        n = len(signal)
        if n < 4:
            return signal

        src_x = np.arange(n, dtype=np.float32)
        warped_x = np.clip(src_x * factor, 0, n - 1)
        shifted = np.interp(warped_x, src_x, signal).astype(np.float32)
        mix = 0.18 + ((amount - 1.0) / 9.0) * 0.30
        return signal * (1.0 - mix) + shifted * mix
