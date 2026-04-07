import numpy as np
from .base import BaseEffect


class MegafonEffect(BaseEffect):
    def __init__(self, samplerate=48000):
        self.samplerate = samplerate

    def _intensity(self, value):
        v = float(value)
        return max(0.0, min(1.0, (v - 1.0) / 9.0))

    def _soft_band_mask(self, freqs, low_cut, high_cut, edge):
        low_start = max(0.0, low_cut - edge)
        low_end = low_cut + edge
        high_start = max(0.0, high_cut - edge)
        high_end = high_cut + edge

        if low_end > low_start:
            low_ramp = (freqs - low_start) / (low_end - low_start)
            low_ramp = np.clip(low_ramp, 0.0, 1.0)
        else:
            low_ramp = np.where(freqs >= low_cut, 1.0, 0.0)

        if high_end > high_start:
            high_ramp = (high_end - freqs) / (high_end - high_start)
            high_ramp = np.clip(high_ramp, 0.0, 1.0)
        else:
            high_ramp = np.where(freqs <= high_cut, 1.0, 0.0)

        return (low_ramp * high_ramp).astype(np.float32)

    def process(self, signal, state):
        if signal is None:
            return signal

        if not getattr(state, "megafon_on", False) or not state.fx_master_on:
            return signal

        n = len(signal)
        if n == 0:
            return signal

        amount = self._intensity(getattr(state, "megafon", 1.0))

        spectrum = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(n, d=1.0 / self.samplerate)
        mask = self._soft_band_mask(freqs, low_cut=420.0, high_cut=3200.0, edge=180.0)
        spectrum *= mask

        presence_center = 1850.0
        presence_width = 700.0
        presence_gain = 1.0 + 0.30 * amount
        presence_curve = 1.0 + (presence_gain - 1.0) * np.exp(
            -0.5 * ((freqs - presence_center) / max(1.0, presence_width)) ** 2
        )
        spectrum *= presence_curve

        processed = np.fft.irfft(spectrum, n=n)
        processed *= 0.88

        drive = 1.10 + 0.45 * amount
        shaped = np.tanh(processed * drive)

        wet = 0.62 + 0.18 * amount
        out = shaped * wet + signal * (1.0 - wet)

        return np.clip(out, -1.0, 1.0)
