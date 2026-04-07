import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys
import subprocess
import ctypes
from core.settings import load_settings, save_settings
from core.version import APP_VERSION
from core.state import AppState
from gui.windows.main import MainWindow

try:
    ctypes.windll.user32.DisableProcessWindowsGhosting()
except Exception:
    pass


class VoiceFXApp:
    def _resolve_icon_path(self, filename):
        base_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(base_dir, "assets", "icons", filename),
            os.path.join(base_dir, "assets", filename),
        ]
        for path in candidates:
            if os.path.exists(path):
                return os.path.abspath(path)
        return os.path.abspath(candidates[0])

    def __init__(self):
        self.gui = None
        self.stream_manager = None
        self.hotkeys = None
        self._update_thread = None

        self.settings = load_settings()
        if self.settings.get("app_version") != APP_VERSION:
            self.settings["app_version"] = APP_VERSION
            save_settings(self.settings)
        self.state = AppState(self.settings)
        self.gui = MainWindow(self)

    def run(self):
        def heavy_initialization():
            threading.Thread(target=self._ensure_desktop_shortcut, daemon=True).start()

            if not self.stream_manager:
                from audio.stream_manager import StreamManager
                self.stream_manager = StreamManager(self)
            if self.stream_manager:
                self.stream_manager.start()
            if not self.hotkeys:
                from core.hotkeys import HotkeyManager
                self.hotkeys = HotkeyManager(self)
            if self.hotkeys:
                self.hotkeys.register()
            self.check_updates_async()

        def start_runtime():
            try:
                self.gui.root.after(500, heavy_initialization)
            except Exception:
                heavy_initialization()

        self.gui.run(on_ready=start_runtime)

    def _ensure_desktop_shortcut(self):
        try:
            if self.settings.get("shortcut_created"):
                return

            exe_path = sys.executable
            if not exe_path.lower().endswith(".exe"):
                return

            icon_path = self._resolve_icon_path("icon.ico")
            if not os.path.exists(icon_path):
                return

            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "VOICE FX PRO.lnk")

            ps = (
                "$W = New-Object -ComObject WScript.Shell; "
                f"$S = $W.CreateShortcut('{shortcut_path}'); "
                f"$S.TargetPath = '{exe_path}'; "
                f"$S.IconLocation = '{icon_path}'; "
                "$S.Save()"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                check=False,
                capture_output=True,
                text=True,
            )

            self.settings["shortcut_created"] = True
            save_settings(self.settings)
        except Exception:
            pass

    def _show_splash(self):
        if not getattr(sys, "frozen", False):
            return
        try:
            splash = tk.Tk()
            splash.overrideredirect(True)
            splash.configure(bg="#0f0f14")

            icon_path = self._resolve_icon_path("icon.png")
            img = None
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)

            if img:
                label = tk.Label(splash, image=img, bg="#0f0f14")
                label.image = img
                label.pack(padx=24, pady=24)
            else:
                label = tk.Label(splash, text="VOICE FX PRO", fg="white", bg="#0f0f14")
                label.pack(padx=24, pady=24)

            splash.update_idletasks()
            w = splash.winfo_width()
            h = splash.winfo_height()
            x = (splash.winfo_screenwidth() - w) // 2
            y = (splash.winfo_screenheight() - h) // 2
            splash.geometry(f"{w}x{h}+{x}+{y}")
            splash.attributes("-alpha", 0.0)

            def fade(step=0):
                alpha = min(1.0, step / 10.0)
                splash.attributes("-alpha", alpha)
                if step < 10:
                    splash.after(30, fade, step + 1)
                else:
                    splash.after(350, splash.destroy)

            fade()
            splash.mainloop()
        except Exception:
            pass

    def check_updates_async(self):
        if not getattr(sys, "frozen", False):
            return
        if self._update_thread and self._update_thread.is_alive():
            return
        self._update_thread = threading.Thread(target=self._check_updates_worker, daemon=True)
        self._update_thread.start()

    def _check_updates_worker(self):
        from core.updater import check_for_update
        info = check_for_update(APP_VERSION, "https://raw.githubusercontent.com/shaker315/voicefx/main/version.json")
        if not info:
            return

        def prompt():
            res = messagebox.askyesno(
                "Aktualizacja",
                f"Dostępna nowa wersja {info['version']}. Zainstalować teraz?",
            )
            if not res:
                return
            self.stream_manager.stop()
            cancel_event = threading.Event()
            try:
                self.gui.show_loading_screen(
                    title_text="Pobieranie aktualizacji",
                    status_text="Przygotowanie...",
                    show_cancel=True,
                )
                self.gui.set_loading_progress(0, smooth=False)
                self.gui.set_loading_cancel_enabled(True)
                def on_cancel():
                    cancel_event.set()
                    try:
                        self.gui.set_loading_status("Anulowanie...")
                        self.gui.set_loading_cancel_enabled(False)
                    except Exception:
                        pass
                self.gui.set_loading_cancel_callback(on_cancel)
                self.gui.root.update_idletasks()
            except Exception:
                pass

            def progress_cb(percent, downloaded, total, speed=0):
                def ui():
                    if total > 0:
                        status = "Pobieranie aktualizacji..."
                        self.gui.set_loading_indeterminate(False)
                        self.gui.set_loading_details(downloaded, total, speed)
                    else:
                        status = "Pobieranie..."
                        self.gui.set_loading_indeterminate(True, status_text=status)
                        self.gui.set_loading_details(downloaded, total, speed)
                        return
                    self.gui.set_loading_progress(percent, status_text=status, smooth=True)
                try:
                    self.gui.root.after(0, ui)
                except Exception:
                    pass

            def status_cb(text):
                try:
                    self.gui.root.after(0, lambda: self.gui.set_loading_status(text))
                except Exception:
                    pass

            def update_worker():
                from core.updater import start_update
                ok, err, launched_installer = start_update(
                    info["url"],
                    progress_cb=progress_cb,
                    status_cb=status_cb,
                    cancel_event=cancel_event,
                )

                def done():
                    if not ok:
                        try:
                            self.gui.set_loading_cancel_enabled(False)
                            self.gui.hide_loading_screen()
                        except Exception:
                            pass
                        if err == "Anulowano":
                            messagebox.showinfo("Aktualizacja", "Pobieranie anulowane.")
                            return
                        messagebox.showerror(
                            "Aktualizacja",
                            f"Nie udało się pobrać aktualizacji.\n{err}",
                        )
                        return
                    self.gui.root.destroy()

                try:
                    self.gui.root.after(0, done)
                except Exception:
                    pass

            threading.Thread(target=update_worker, daemon=True).start()

        try:
            self.gui.root.after(0, prompt)
        except Exception:
            pass
