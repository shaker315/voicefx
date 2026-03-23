import json
import os

_APP_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "VoiceFX")
SETTINGS_FILE = os.path.join(_APP_DIR, "settings.json")

KEY_PATHS = {
    "distortion_on": ("fx", "distortion_on"),
    "saturation_on": ("fx", "saturation_on"),
    "bass_on": ("fx", "bass_on"),
    "shift_on": ("fx", "shift_on"),
    "bitcrusher_on": ("fx", "bitcrusher_on"),
    "exciter_on": ("fx", "exciter_on"),
    "tube_on": ("fx", "tube_on"),
    "sub_bass_on": ("fx", "sub_bass_on"),
    "echo_on": ("fx", "echo_on"),
    "noise_gate_on": ("fx", "noise_gate_on"),
    "fx_master_on": ("fx", "fx_master_on"),
    "distortion": ("fx", "distortion"),
    "saturation": ("fx", "saturation"),
    "bass_gain": ("fx", "bass_gain"),
    "shift": ("fx", "shift"),
    "bitcrusher": ("fx", "bitcrusher"),
    "exciter": ("fx", "exciter"),
    "tube": ("fx", "tube"),
    "sub_bass": ("fx", "sub_bass"),
    "echo": ("fx", "echo"),
    "noise_gate_threshold": ("fx", "noise_gate_threshold"),
    "mic_enabled": ("audio", "mic_enabled"),
    "monitor_on": ("audio", "monitor_on"),
    "volume": ("audio", "volume"),
    "volume_fx_on": ("audio", "volume_fx_on"),
    "volume_fx_off": ("audio", "volume_fx_off"),
    "monitor_volume": ("audio", "monitor_volume"),
    "hotkey_true_mic_mute": ("hotkeys", "true_mic_mute"),
    "hotkey_mic_mute": ("hotkeys", "mic_mute"),
    "hotkey_monitor_mute": ("hotkeys", "monitor_mute"),
    "window_width": ("gui", "window_width"),
    "window_height": ("gui", "window_height"),
    "window_x": ("gui", "window_x"),
    "window_y": ("gui", "window_y"),
    "show_meter": ("gui", "show_meter"),
    "show_effect_distortion": ("gui", "show_effect_distortion"),
    "show_effect_saturation": ("gui", "show_effect_saturation"),
    "show_effect_bass": ("gui", "show_effect_bass"),
    "show_effect_shift": ("gui", "show_effect_shift"),
    "show_effect_bitcrusher": ("gui", "show_effect_bitcrusher"),
    "show_effect_exciter": ("gui", "show_effect_exciter"),
    "show_effect_tube": ("gui", "show_effect_tube"),
    "show_effect_sub_bass": ("gui", "show_effect_sub_bass"),
    "show_effect_echo": ("gui", "show_effect_echo"),
    "shortcut_created": ("gui", "shortcut_created"),
    "theme": ("gui", "theme"),
    "default_input_device": ("devices", "default_input_device"),
    "default_output_device": ("devices", "default_output_device"),
}

default_settings = {
    "distortion_on": False,
    "saturation_on": False,
    "bass_on": False,
    "shift_on": False,
    "bitcrusher_on": False,
    "exciter_on": False,
    "tube_on": False,
    "sub_bass_on": False,
    "echo_on": False,
    "noise_gate_on": True,
    "fx_master_on": True,
    "mic_enabled": True,
    "monitor_on": False,
    "distortion": 1.2,
    "saturation": 1.0,
    "bass_gain": 1.5,
    "shift": 1.0,
    "bitcrusher": 1.0,
    "exciter": 1.0,
    "tube": 1.0,
    "sub_bass": 1.0,
    "echo": 1.0,
    "noise_gate_threshold": 0.020,
    "volume": 1.0,
    "volume_fx_on": 1.0,
    "volume_fx_off": 1.0,
    "monitor_volume": 1.0,
    "hotkey_true_mic_mute": "F10",
    "hotkey_mic_mute": "F8",
    "hotkey_monitor_mute": "F9",
    "window_width": 560,
    "window_height": 750,
    "window_x": None,
    "window_y": None,
    "show_meter": True,
    "show_effect_distortion": True,
    "show_effect_saturation": True,
    "show_effect_bass": True,
    "show_effect_shift": True,
    "show_effect_bitcrusher": True,
    "show_effect_exciter": True,
    "show_effect_tube": True,
    "show_effect_sub_bass": True,
    "show_effect_echo": True,
    "shortcut_created": False,
    "theme": "dark",
    "default_input_device": None,
    "default_output_device": None,
}


def _is_nested_settings(payload):
    return any(
        isinstance(payload.get(section), dict)
        for section in ("fx", "audio", "hotkeys", "gui", "devices")
    )


def _flatten_settings(payload):
    flat = default_settings.copy()

    if not isinstance(payload, dict):
        return flat

    if _is_nested_settings(payload):
        for flat_key, (section, nested_key) in KEY_PATHS.items():
            section_obj = payload.get(section, {})
            if isinstance(section_obj, dict) and nested_key in section_obj:
                flat[flat_key] = section_obj[nested_key]

        fx_obj = payload.get("fx", {})
        if isinstance(fx_obj, dict):
            if "saturation_on" not in fx_obj and "przester_on" in fx_obj:
                flat["saturation_on"] = fx_obj["przester_on"]
            if "saturation" not in fx_obj and "przester" in fx_obj:
                flat["saturation"] = fx_obj["przester"]
        return flat

    for key in default_settings:
        if key in payload:
            flat[key] = payload[key]

    if "saturation_on" not in payload and "przester_on" in payload:
        flat["saturation_on"] = payload["przester_on"]
    if "saturation" not in payload and "przester" in payload:
        flat["saturation"] = payload["przester"]
    return flat


def _nest_settings(flat):
    grouped = {
        "fx": {},
        "audio": {},
        "hotkeys": {},
        "gui": {},
        "devices": {},
    }

    for flat_key, default_val in default_settings.items():
        section, nested_key = KEY_PATHS[flat_key]
        grouped[section][nested_key] = flat.get(flat_key, default_val)

    return grouped

def load_settings():
    data = default_settings.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                loaded = json.load(f)
            data.update(_flatten_settings(loaded))
        except:
            pass
        return data

    try:
        os.makedirs(_APP_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(_nest_settings(data), f, indent=4)
    except:
        pass
    return data

def save_settings(settings):
    flat = _flatten_settings(settings)
    nested = _nest_settings(flat)

    os.makedirs(_APP_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(nested, f, indent=4)
