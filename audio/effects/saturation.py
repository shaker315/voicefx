import numpy as np
from .base import BaseEffect


class SaturationEffect(BaseEffect):
    def process(self, signal, state):
        if not state.saturation_on or not state.fx_master_on:
            return signal

        drive = max(1.0, float(state.saturation))
        wet = np.tanh(signal * drive)
        blend = 0.55
        return signal * (1.0 - blend) + wet * blend
