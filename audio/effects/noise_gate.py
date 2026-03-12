import math
import numpy as np
from .base import BaseEffect


class NoiseGateEffect(BaseEffect):
    def __init__(self, samplerate=48000):
        self.samplerate = max(1, int(samplerate))
        self.env = 0.0
        self.gain = 1.0

    def process(self, signal, state):
        if not state.noise_gate_on or not state.fx_master_on:
            return signal

        threshold = float(state.noise_gate_threshold)
        threshold = max(0.001, min(0.20, threshold))

        floor_gain = 0.03
        curve = 1.7
        attack_ms = 10.0
        release_ms = 220.0
        env_ms = 10.0

        env_alpha = math.exp(-1.0 / (self.samplerate * env_ms / 1000.0))
        att_alpha = math.exp(-1.0 / (self.samplerate * attack_ms / 1000.0))
        rel_alpha = math.exp(-1.0 / (self.samplerate * release_ms / 1000.0))

        out = np.empty_like(signal)

        for i, x in enumerate(signal):
            amp = abs(float(x))
            self.env = env_alpha * self.env + (1.0 - env_alpha) * amp

            if self.env >= threshold:
                target = 1.0
            else:
                n = max(0.0, min(1.0, self.env / threshold))
                target = floor_gain + (1.0 - floor_gain) * (n ** curve)

            alpha = att_alpha if target > self.gain else rel_alpha
            self.gain = alpha * self.gain + (1.0 - alpha) * target
            out[i] = x * self.gain

        return out
