import numpy as np

from .effects.distortion import DistortionEffect
from .effects.bass import BassBoostEffect
from .effects.saturation import SaturationEffect
from .effects.noise_gate import NoiseGateEffect
from .effects.compressor import CompressorEffect
from .effects.limiter import SoftLimiterEffect


class AudioEngine:
    def __init__(self, state, samplerate=48000):
        self.state = state
        self.samplerate = samplerate

        self.distortion = DistortionEffect()
        self.saturation = SaturationEffect()
        self.bass = BassBoostEffect(samplerate=samplerate)
        self.noise_gate = NoiseGateEffect(samplerate=samplerate)
        self.compressor = CompressorEffect()
        self.limiter = SoftLimiterEffect()

        self.effects = [
            self.distortion,
            self.saturation,
            self.compressor,
            self.bass
        ]

    def process(self, indata):

        audio = indata[:, 0]
        processed = audio.copy()

        if self.state.true_mute_active:
            return np.zeros_like(audio).astype(np.float32).reshape(-1, 1)

        if not self.state.mic_enabled:
            processed = np.zeros_like(processed)

        if self.state.fx_master_on:
            if self.state.noise_gate_on:
                processed = self.noise_gate.process(processed, self.state)

            if self.state.bass_on:
                processed = self.bass.process(processed, self.state)

            if self.state.distortion_on:
                processed = self.distortion.process(processed, self.state)
            if self.state.saturation_on:
                processed = self.saturation.process(processed, self.state)

        volume = self.state.volume

        if not self.state.fx_master_on and volume > 2.0:
            volume = 2.0
            self.state.volume = 2.0

        processed *= volume

        processed = self.compressor.process(processed, self.state)
        processed = self.limiter.process(processed, self.state)

        current_rms = np.sqrt(np.mean(processed ** 2))
        self.state.smoothed_rms = self.state.smoothed_rms * 0.9 + current_rms * 0.1

        peak = np.max(np.abs(processed))
        self.state.peak_level = max(peak, self.state.peak_level * 0.92)

        processed = np.clip(processed, -1.0, 1.0)
        return processed.astype(np.float32).reshape(-1, 1)
