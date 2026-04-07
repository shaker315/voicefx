import numpy as np
from .base import BaseEffect


class OldRadioEffect(BaseEffect):
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

        if not getattr(state, "stare_radio_on", False) or not state.fx_master_on:
            return signal

        n = len(signal)
        if n == 0:
            return signal

        amount = self._intensity(getattr(state, "stare_radio", 1.0))

        spectrum = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(n, d=1.0 / self.samplerate)
        mask = self._soft_band_mask(freqs, low_cut=360.0, high_cut=2350.0, edge=160.0)
        spectrum *= mask

        processed = np.fft.irfft(spectrum, n=n)

        bits = int(round(7.0 - 3.0 * amount))
        bits = max(4, min(7, bits))
        levels = float(2 ** bits)
        processed = np.round(processed * levels) / levels

        env = float(np.sqrt(np.mean(processed * processed)))
        env_factor = min(1.0, env / 0.10)
        noise_amp = (0.0012 + 0.0032 * amount) * (0.35 + 0.65 * env_factor)
        noise = np.random.normal(0.0, noise_amp, size=signal.shape)
        processed = processed + noise

        drive = 1.05 + 0.35 * amount
        processed = np.tanh(processed * drive)

        wet = 0.62 + 0.22 * amount
        out = processed * wet + signal * (1.0 - wet)

        return np.clip(out, -1.0, 1.0)
