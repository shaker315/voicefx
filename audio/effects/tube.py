import numpy as np

from .base import BaseEffect


class TubeEffect(BaseEffect):
    def process(self, signal, state):
        if not state.tube_on or not state.fx_master_on:
            return signal

        amount = max(1.0, min(10.0, float(state.tube)))
        drive = 1.1 + ((amount - 1.0) / 9.0) * 4.2
        asym = 0.08 + ((amount - 1.0) / 9.0) * 0.22

        x = signal * drive
        shaped = np.tanh(x + asym) - np.tanh(asym)
        makeup = 1.0 / max(0.35, np.max(np.abs(shaped)) if np.max(np.abs(shaped)) > 0 else 1.0)
        mix = 0.20 + ((amount - 1.0) / 9.0) * 0.45
        return signal * (1.0 - mix) + (shaped * makeup) * mix
