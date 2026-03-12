import numpy as np
from .base import BaseEffect


class DistortionEffect(BaseEffect):
    def process(self, signal, state):

        if not state.distortion_on or not state.fx_master_on:
            return signal

        drive = state.distortion

        processed = np.tanh(signal * drive)

        return processed
