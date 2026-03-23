import keyboard
from core.settings import save_settings

class HotkeyManager:
    def __init__(self, app):
        self.app = app
        self.handlers = []

    def clear(self):
        for h in self.handlers:
            keyboard.remove_hotkey(h)
        self.handlers.clear()

    def register(self):
        self.clear()
        mic_hotkey = self.app.settings["hotkey_mic_mute"]
        monitor_hotkey = self.app.settings["hotkey_monitor_mute"]
        true_mute_hotkey = self.app.settings["hotkey_true_mic_mute"]

        if mic_hotkey:
            h = keyboard.add_hotkey(mic_hotkey, self.toggle_fx_master)
            self.handlers.append(h)
        if monitor_hotkey:
            h = keyboard.add_hotkey(monitor_hotkey, self.toggle_monitor)
            self.handlers.append(h)
        if true_mute_hotkey:
            h = keyboard.add_hotkey(true_mute_hotkey, self.toggle_true_mute)
            self.handlers.append(h)

    def toggle_fx_master(self):
        state = self.app.state
        if state.true_mute_active:
            return
        state.toggle_fx_master()
        self.save_and_update()

    def toggle_monitor(self):
        state = self.app.state

        if state.true_mute_active:
            return

        state.toggle_monitor()

        if self.app.stream_manager:
            self.app.stream_manager.update_monitor_state()

        self.save_and_update()

    def toggle_true_mute(self):
        state = self.app.state
        state.toggle_true_mute()

        if self.app.stream_manager:
            self.app.stream_manager.update_monitor_state()
        self.save_and_update()

    def save_and_update(self):
        s = self.app.state
        settings = self.app.settings

        settings["distortion_on"] = s.distortion_on
        settings["saturation_on"] = s.saturation_on
        settings["bass_on"] = s.bass_on
        settings["shift_on"] = s.shift_on
        settings["bitcrusher_on"] = s.bitcrusher_on
        settings["exciter_on"] = s.exciter_on
        settings["tube_on"] = s.tube_on
        settings["sub_bass_on"] = s.sub_bass_on
        settings["echo_on"] = s.echo_on
        settings["noise_gate_on"] = s.noise_gate_on
        settings["fx_master_on"] = s.fx_master_on
        settings["monitor_on"] = s.monitor_on
        settings["volume"] = s.volume
        settings["volume_fx_on"] = s.volume_fx_on
        settings["volume_fx_off"] = s.volume_fx_off
        settings["monitor_volume"] = s.monitor_volume
        settings["shift"] = s.shift
        settings["bitcrusher"] = s.bitcrusher
        settings["exciter"] = s.exciter
        settings["tube"] = s.tube
        settings["sub_bass"] = s.sub_bass
        settings["echo"] = s.echo
        settings["noise_gate_threshold"] = s.noise_gate_threshold

        save_settings(settings)

        if self.app.gui:
            self.app.gui.root.after(0, self.app.gui.update_icons)
