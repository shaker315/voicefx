import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "distortion_on": False,
    "saturation_on": False,
    "bass_on": False,
    "monitor_volume_on": False,
    "volume_on": False,
    "distortion": 1.2,
    "saturation": 1.0,
    "bass_gain": 1.5,
    "mic_muted": False,
    "volume": 1.0,
    "monitor_volume": 1.0,
    "hotkey_mic_mute": "F8",
    "hotkey_monitor_mute": "F9",
    "window_width": 560,
    "window_height": 750,
    "window_x": None,
    "window_y": None,
    "default_input_device": None,
    "default_output_device": None,
}
