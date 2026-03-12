import sounddevice as sd
import tkinter as tk
from tkinter import messagebox
import threading
from core.updater import check_for_update, start_update
from core.settings import load_settings, save_settings
from core.version import APP_VERSION
from core.state import AppState
from core.hotkeys import HotkeyManager
from audio.stream_manager import StreamManager
from gui.main_window import MainWindow


class VoiceFXApp:

    def __init__(self):
        self.settings = load_settings()
        if self.settings.get("app_version") != APP_VERSION:
            self.settings["app_version"] = APP_VERSION
            save_settings(self.settings)
        self.state = AppState(self.settings)
        self.gui = None
        if not self._detect_vb_cable():
            self._show_vb_missing_dialog()
            raise SystemExit(1)
        self.stream_manager = StreamManager(self)
        self.hotkeys = HotkeyManager(self)
        self.gui = MainWindow(self)
        self._update_thread = None

    def run(self):
        self.stream_manager.start()
        self.hotkeys.register()
        self.check_updates_async()
        self.gui.run()

    def _detect_vb_cable(self):
        try:
            devices = sd.query_devices()
        except Exception:
            return False

        for d in devices:
            name = str(d.get("name", "")).lower()
            if "cable input" in name or "vb-audio" in name:
                return True
        return False

    def _show_vb_missing_dialog(self):
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Brak VB-CABLE",
            "Nie wykryto VB-CABLE (CABLE Input). Pobierz i zainstaluj sterownik, a potem uruchom aplikacje ponownie.",
        )
        root.destroy()

    def check_updates_async(self):
        if self._update_thread and self._update_thread.is_alive():
            return
        self._update_thread = threading.Thread(target=self._check_updates_worker, daemon=True)
        self._update_thread.start()

    def _check_updates_worker(self):
        info = check_for_update(APP_VERSION, "https://raw.githubusercontent.com/shaker315/voicefx/main/version.json")
        if not info:
            return

        def prompt():
            res = messagebox.askyesno(
                "Aktualizacja",
                f"Dostepna nowa wersja {info['version']}. Zainstalowac teraz?",
            )
            if not res:
                return
            self.stream_manager.stop()
            ok, err = start_update(info["url"])
            if not ok:
                messagebox.showerror("Aktualizacja", f"Nie udalo sie pobrac aktualizacji.\n{err}")
            else:
                self.gui.root.destroy()

        try:
            self.gui.root.after(0, prompt)
        except Exception:
            pass
