import numpy as np

from .effects.distortion import DistortionEffect
from .effects.bass import BassBoostEffect
from .effects.saturation import SaturationEffect
from .effects.shift import ShiftEffect
from .effects.bitcrusher import BitcrusherEffect
from .effects.exciter import ExciterEffect
from .effects.tube import TubeEffect
from .effects.sub_bass import SubBassEffect
from .effects.echo import EchoEffect
from .effects.noise_gate import NoiseGateEffect
from .effects.compressor import CompressorEffect
from .effects.limiter import SoftLimiterEffect
from .effects.megafon import MegafonEffect
from .effects.old_radio import OldRadioEffect


class AudioEngine:
    def __init__(self, state, samplerate=48000):
        self.state = state
        self.samplerate = samplerate

        self.distortion = DistortionEffect()
        self.saturation = SaturationEffect()
        self.shift = ShiftEffect()
        self.bitcrusher = BitcrusherEffect()
        self.exciter = ExciterEffect()
        self.tube = TubeEffect()
        self.sub_bass = SubBassEffect(samplerate=samplerate)
        self.echo = EchoEffect(samplerate=samplerate)
        self.bass = BassBoostEffect(samplerate=samplerate)
        self.megafon = MegafonEffect(samplerate=samplerate)
        self.stare_radio = OldRadioEffect(samplerate=samplerate)
        self.noise_gate = NoiseGateEffect(samplerate=samplerate)
        self.compressor = CompressorEffect()
        self.limiter = SoftLimiterEffect()

        self.effects = [
            self.distortion,
            self.saturation,
            self.compressor,
            self.bass,
            self.megafon,
            self.stare_radio,
        ]

    def process(self, indata):

        audio = indata[:, 0]
        processed = audio.copy()
        meter_audio = audio.copy()

        if self.state.true_mute_active:
            self.state.smoothed_rms = self.state.smoothed_rms * 0.9
            self.state.peak_level = self.state.peak_level * 0.92
            return np.zeros_like(audio).astype(np.float32).reshape(-1, 1)

        if not self.state.mic_enabled:
            processed = np.zeros_like(processed)
            meter_audio = np.zeros_like(meter_audio)

        if self.state.noise_gate_on:
            processed = self.noise_gate.process(processed, self.state)

        if self.state.fx_master_on:
            if self.state.bass_on:
                processed = self.bass.process(processed, self.state)

            if self.state.distortion_on:
                processed = self.distortion.process(processed, self.state)
            if self.state.saturation_on:
                processed = self.saturation.process(processed, self.state)
            if self.state.shift_on:
                processed = self.shift.process(processed, self.state)
            if self.state.bitcrusher_on:
                processed = self.bitcrusher.process(processed, self.state)
            if self.state.exciter_on:
                processed = self.exciter.process(processed, self.state)
            if self.state.tube_on:
                processed = self.tube.process(processed, self.state)
            if self.state.sub_bass_on:
                processed = self.sub_bass.process(processed, self.state)
            if self.state.echo_on:
                processed = self.echo.process(processed, self.state)
            if self.state.megafon_on:
                processed = self.megafon.process(processed, self.state)
            if self.state.stare_radio_on:
                processed = self.stare_radio.process(processed, self.state)

        volume = self.state.volume

        if not self.state.fx_master_on and volume > 2.0:
            volume = 2.0
            self.state.volume = 2.0

        processed *= volume

        processed = self.compressor.process(processed, self.state)
        processed = self.limiter.process(processed, self.state)

        current_rms = np.sqrt(np.mean(meter_audio ** 2))
        self.state.smoothed_rms = self.state.smoothed_rms * 0.9 + current_rms * 0.1

        peak = np.max(np.abs(meter_audio))
        self.state.peak_level = max(peak, self.state.peak_level * 0.92)

        processed = np.clip(processed, -1.0, 1.0)
        return processed.astype(np.float32).reshape(-1, 1)
