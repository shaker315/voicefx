class AppState:
    def __init__(self, settings):
        self.settings = settings
        self.smoothed_rms = 0.0
        self.peak_level = 0.0

        self.default_input_device = settings.get("default_input_device", None)
        self.default_output_device = settings.get("default_output_device", None)

        self.distortion_on = settings.get("distortion_on", False)
        self.saturation_on = settings.get(
            "saturation_on", settings.get("przester_on", False)
        )
        self.bass_on = settings.get("bass_on", False)
        self.noise_gate_on = settings.get("noise_gate_on", True)
        self.distortion = settings.get("distortion", 1.2)
        self.saturation = settings.get("saturation", settings.get("przester", 1.0))
        self.bass_gain = settings.get("bass_gain", 1.5)
        self.noise_gate_threshold = settings.get("noise_gate_threshold", 0.020)
        base_volume = settings.get("volume", 1.0)
        self.volume_fx_on = settings.get("volume_fx_on", base_volume)
        self.volume_fx_off = settings.get("volume_fx_off", min(base_volume, 2.0))
        self.volume = base_volume
        self.monitor_volume = settings.get("monitor_volume", 1.0)

        self.compressor_threshold = 0.25
        self.compressor_ratio = 4.0

        self.fx_master_on = settings.get("fx_master_on", True)
        self.monitor_on = settings.get("monitor_on", False)
        self.mic_enabled = True
        self.volume = self.volume_fx_on if self.fx_master_on else self.volume_fx_off

        self.true_mute_active = False
        self._pre_mute_state = {}

        self._pre_fx_state = {
            "distortion_on": self.distortion_on,
            "saturation_on": self.saturation_on,
            "bass_on": self.bass_on,
            "noise_gate_on": self.noise_gate_on,
        }

        self.window_width = settings.get("window_width", 560)
        self.window_height = settings.get("window_height", 750)
        self.window_x = settings.get("window_x")
        self.window_y = settings.get("window_y")
        self.show_meter = settings.get("show_meter", True)

        self.fx_locked = False
        self.monitor_locked = False
        self._pre_fx_state_gui = {
            "distortion_on": self.distortion_on,
            "saturation_on": self.saturation_on,
            "bass_on": self.bass_on,
            "noise_gate_on": self.noise_gate_on,
        }
        self._pre_monitor_state_gui = self.monitor_on
        self._enforce_volume_limit()

    def _enforce_volume_limit(self):
        if self.volume_fx_off > 2.0:
            self.volume_fx_off = 2.0
        if not self.fx_master_on and self.volume > 2.0:
            self.volume = 2.0

    def set_volume(self, value):
        self.volume = value
        if self.fx_master_on:
            self.volume_fx_on = value
        else:
            self.volume_fx_off = value
        self._enforce_volume_limit()

    def toggle_fx_master(self):
        if self.true_mute_active:
            return

        if self.fx_master_on:
            self._pre_fx_state = {
                "distortion_on": self.distortion_on,
                "saturation_on": self.saturation_on,
                "bass_on": self.bass_on,
                "noise_gate_on": self.noise_gate_on,
            }
            self.distortion_on = False
            self.saturation_on = False
            self.bass_on = False
            self.noise_gate_on = False
            self.fx_master_on = False
            self.volume_fx_on = self.volume
            self.volume = self.volume_fx_off

            self.fx_locked = True
            self._enforce_volume_limit()
        else:
            self.distortion_on = self._pre_fx_state.get("distortion_on", False)
            self.saturation_on = self._pre_fx_state.get("saturation_on", False)
            self.bass_on = self._pre_fx_state.get("bass_on", False)
            self.noise_gate_on = self._pre_fx_state.get("noise_gate_on", True)
            self.fx_master_on = True
            self.volume_fx_off = self.volume
            self.volume = self.volume_fx_on

            self.fx_locked = False

    def toggle_monitor(self):
        if self.true_mute_active:
            return
        self.monitor_on = not self.monitor_on

    def toggle_true_mute(self):
        if not self.true_mute_active:
            self._pre_mute_state = {
                "mic_enabled": self.mic_enabled,
                "monitor_on": self.monitor_on,
                "fx_master_on": self.fx_master_on,
                "distortion_on": self.distortion_on,
                "saturation_on": self.saturation_on,
                "bass_on": self.bass_on,
                "noise_gate_on": self.noise_gate_on,
            }
            self.mic_enabled = False
            self.monitor_on = False
            self.fx_master_on = False
            self.distortion_on = False
            self.saturation_on = False
            self.bass_on = False
            self.noise_gate_on = False
            self.true_mute_active = True

            self.fx_locked = True
            self.monitor_locked = True
        else:
            self.mic_enabled = self._pre_mute_state.get("mic_enabled", True)
            self.monitor_on = self._pre_mute_state.get("monitor_on", False)
            self.fx_master_on = self._pre_mute_state.get("fx_master_on", True)
            self.distortion_on = self._pre_mute_state.get("distortion_on", False)
            self.saturation_on = self._pre_mute_state.get("saturation_on", False)
            self.bass_on = self._pre_mute_state.get("bass_on", False)
            self.noise_gate_on = self._pre_mute_state.get("noise_gate_on", True)
            self.true_mute_active = False

            self.fx_locked = False
            self.monitor_locked = False

    def reset_fx(self):
        self.distortion = 1.0
        self.saturation = 1.0
        self.bass_gain = 1.0
        self.noise_gate_threshold = 0.020
        self.monitor_volume = 1.0
        self.volume_fx_on = 1.0
        self.volume_fx_off = 1.0
        self.volume = 1.0
    
    def toggle_meter(self):
        self.show_meter = not self.show_meter
