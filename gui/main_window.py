import os
import tkinter as tk
from gui.components.tooltip import Tooltip
from gui.components.slider import ModernSlider
from gui.components.meter import MasterMeter
from gui.settings_window import SettingsWindow
from gui.components.scrollbar_style import UltraThinScrollbar
from gui.loading.loading_app_screen import AppLoadingScreen
from gui.loading.loading_update_screen import UpdateLoadingScreen
from gui.theme import get_theme


class MainWindow:
    def __init__(self, app):
        self.app = app
        self.app_state = app.state
        self.settings = app.settings
        self.meter = None
        self.sliders = []
        self.theme = get_theme(self.settings.get("theme", "dark"))

        self.root = tk.Tk()
        self.root.title("VOICE FX PRO")
        self.root.configure(bg=self.theme["bg_root"])
        self.root.withdraw()
        self._set_app_icon()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app_loading_screen = AppLoadingScreen(self.root, self.theme)
        self.update_loading_screen = UpdateLoadingScreen(self.root, self.theme)
        self._active_loading_screen = None

        self.setup_geometry()
        self.show_app_loading_screen(
            title_text="Wczytywanie...",
            status_text="Przygotowanie interfejsu...",
            show_cancel=False,
        )
        self.set_loading_progress(0, smooth=False)
        self.root.deiconify()
        self.root.update_idletasks()
        self.root.update()

        self.create_layout()
        self.create_top_bar()
        self.create_sliders()
        self.create_meter()

        self.root.bind("<Configure>", self.on_configure)

        self.refresh_loop()
        self.root.update_idletasks()
        self.update_scrollregion()
        self.hide_loading_screen()
        # Ensure mouse wheel works even if the cursor never re-enters after loading overlay
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)


    def setup_geometry(self):
        width = self.app_state.window_width
        height = self.app_state.window_height

        x = self.app_state.window_x
        y = self.app_state.window_y

        if x is None or y is None:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = int((screen_width - width) / 2)
            y = int((screen_height - height) / 2)

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(350, 300)

    def _set_app_icon(self):
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            ico_path = os.path.join(base_dir, "assets", "icon.ico")
            png_path = os.path.join(base_dir, "assets", "icon.png")

            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)

            if os.path.exists(png_path):
                self._icon_img = tk.PhotoImage(file=png_path)
                self.root.iconphoto(False, self._icon_img)
        except Exception:
            pass

    def create_layout(self):
        self.container = tk.Frame(self.root, bg=self.theme["bg_root"])
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.container,
            bg=self.theme["bg_root"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.scrollbar = UltraThinScrollbar(
            self.container,
            target_canvas=self.canvas,
            width=3,
            thumb_color=self.theme["scrollbar_thumb"],
            auto_hide_delay=1500,
        )

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.main_frame = tk.Frame(self.canvas, bg=self.theme["bg_root"])
        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.main_frame,
            anchor="nw",
        )

        self.main_frame.bind("<Configure>", self.update_scrollregion)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_configure(self, event):
        if self.root.state() == "iconic":
            if self.meter and self.meter.winfo_ismapped():
                self.meter.grid_remove()
        else:
            if self.meter and not self.meter.winfo_ismapped():
                self.meter.grid()
        self.root.after_idle(self.update_scrollregion)

    def on_canvas_configure(self, event):
        self.resize_main_frame(event)
        self.root.after_idle(self.update_scrollregion)

    def resize_main_frame(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def update_scrollregion(self, event=None):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return

        self.canvas.configure(scrollregion=bbox)

        content_height = bbox[3] - bbox[1]
        canvas_height = self.canvas.winfo_height()

        if content_height > canvas_height:
            if not self.scrollbar.winfo_ismapped():
                self.scrollbar.place(
                    relx=1.0,
                    rely=0,
                    relheight=1.0,
                    anchor="ne",
                    width=8,
                )
        else:
            if self.scrollbar.winfo_ismapped():
                self.scrollbar.place_forget()
            self.canvas.yview_moveto(0)


    def create_top_bar(self):
        top = tk.Frame(self.main_frame, bg=self.theme["bg_root"], height=60)
        top.grid(row=0, column=0, sticky="ew", pady=10, padx=10)
        top.grid_columnconfigure(0, weight=1)  # left
        top.grid_columnconfigure(1, weight=1)  # center
        top.grid_columnconfigure(2, weight=1)  # right

        self.mic_icon = tk.Label(
            top,
            text="\U0001F3A4",
            font=("Segoe UI", 30),
            bg=self.theme["bg_root"],
            fg=self.theme["accent"] if self.app_state.fx_master_on else self.theme["danger"],
        )
        self.mic_icon.grid(row=0, column=0, sticky="w")  # left
        self.mic_icon.config(cursor="hand2")
        self.mic_icon.bind("<Button-1>", self.toggle_mic_click)
        Tooltip(self.mic_icon, "Efekty")

        self.monitor_icon = tk.Label(
            top,
            text="\U0001F3A7",
            font=("Segoe UI", 30),
            bg=self.theme["bg_root"],
            fg=self.theme["accent"] if self.app_state.monitor_on else self.theme["danger"],
        )
        self.monitor_icon.grid(row=0, column=2, sticky="e")  # right
        Tooltip(self.monitor_icon, "Odsluch")
        self.monitor_icon.config(cursor="hand2")
        self.monitor_icon.bind("<Button-1>", self.toggle_monitor_click)

        settings_btn = tk.Button(
            top,
            text="\u2699\ufe0f",
            font=("Segoe UI", 18),
            bg=self.theme["bg_root"],
            fg=self.theme["fg_primary"],
            activebackground=self.theme["bg_root"],
            activeforeground=self.theme["fg_primary"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            takefocus=0,
            cursor="hand2",
            command=self.open_settings,
        )
        settings_btn.grid(row=0, column=1, sticky="")  # center
        Tooltip(settings_btn, "Ustawienia")

    def update_icons(self):
        state = self.app_state

        if state.true_mute_active:
            self.mic_icon.config(fg=self.theme["fg_muted"])
            self.monitor_icon.config(fg=self.theme["fg_muted"])
            self.mic_icon.config(cursor="arrow")
            self.monitor_icon.config(cursor="arrow")

            for widget in self.main_frame.winfo_children():
                if hasattr(widget, "draw"):
                    widget.draw()
            return

        self.mic_icon.config(fg=self.theme["accent"] if state.fx_master_on else self.theme["danger"])
        self.mic_icon.config(cursor="hand2")

        self.monitor_icon.config(fg=self.theme["accent"] if state.monitor_on else self.theme["danger"])
        self.monitor_icon.config(cursor="hand2")

        for widget in self.main_frame.winfo_children():
            if hasattr(widget, "draw"):
                widget.draw()

    def toggle_mic_click(self, event=None):
        if self.app_state.true_mute_active:
            return

        if event and (event.state & 0x0001):
            self.app_state.toggle_mic_mute()
        else:
            self.app_state.toggle_fx_master()
        self.save_settings()
        self.update_icons()

    def toggle_monitor_click(self, event=None):
        if self.app_state.true_mute_active:
            return

        self.app_state.monitor_on = not self.app_state.monitor_on
        if self.app.stream_manager:
            self.app.stream_manager.update_monitor_state()
        self.save_settings()
        self.update_icons()


    def create_sliders(self):
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.sliders = []
        slider = ModernSlider(
            self.main_frame,
            "Glosnosc mikrofonu",
            self.app_state,
            "volume",
            0.2,
            10.0,
            save_callback=self.save_settings,
            default_value=1,
            theme=self.theme,
        )
        slider.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.sliders.append(slider)

        slider = ModernSlider(
            self.main_frame,
            "Odsluch",
            self.app_state,
            "monitor_volume",
            0.05,
            2.0,
            save_callback=self.save_settings,
            default_value=1,
            theme=self.theme,
        )
        slider.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.sliders.append(slider)

        slider = ModernSlider(
            self.main_frame,
            "Przester",
            self.app_state,
            "distortion",
            1,
            10,
            toggle_attr="distortion_on",
            save_callback=self.save_settings,
            default_value=1,
            theme=self.theme,
        )
        slider.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.sliders.append(slider)

        slider = ModernSlider(
            self.main_frame,
            "Saturacja",
            self.app_state,
            "saturation",
            1,
            10,
            toggle_attr="saturation_on",
            save_callback=self.save_settings,
            default_value=1,
            theme=self.theme,
        )
        slider.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        self.sliders.append(slider)

        slider = ModernSlider(
            self.main_frame,
            "Podbicie basu",
            self.app_state,
            "bass_gain",
            1,
            10,
            toggle_attr="bass_on",
            save_callback=self.save_settings,
            default_value=1,
            theme=self.theme,
        )
        slider.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        self.sliders.append(slider)

        slider = ModernSlider(
            self.main_frame,
            "Bramka szumow",
            self.app_state,
            "noise_gate_threshold",
            0.005,
            0.08,
            toggle_attr="noise_gate_on",
            save_callback=self.save_settings,
            default_value=0.020,
            theme=self.theme,
        )
        slider.grid(row=6, column=0, sticky="ew", padx=10, pady=5)
        self.sliders.append(slider)

        reset_btn = tk.Button(
            self.main_frame,
            text="Reset efektow",
            command=self.reset_fx,
            bg=self.theme["button_bg"],
            fg=self.theme["button_text"],
            activebackground=self.theme["button_bg_hover"],
            activeforeground=self.theme["button_text"],
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=6,
        )
        reset_btn.grid(row=7, column=0, pady=10)

    def reset_fx(self):
        self.app_state.reset_fx()

        for widget in self.main_frame.winfo_children():
            if hasattr(widget, "draw"):
                widget.draw()

        self.save_settings()


    def create_meter(self):
        if self.settings.get("show_meter", True):
            self.meter = MasterMeter(self.main_frame, self.app_state, theme=self.theme)
            self.meter.grid(row=8, column=0, sticky="ew", pady=20, padx=10)
        else:
            self.meter = None

    def update_meter_visibility(self):
        if self.app_state.show_meter:
            if not hasattr(self, "meter") or self.meter is None:
                self.meter = MasterMeter(self.main_frame, self.app_state, theme=self.theme)
                self.meter.grid(row=8, column=0, sticky="ew", pady=20, padx=10)
        else:
            if hasattr(self, "meter") and self.meter:
                self.meter.destroy()
                self.meter = None

        self.root.update_idletasks()
        self.update_scrollregion()
        self.root.after_idle(self.update_scrollregion)

        bbox = self.canvas.bbox("all")
        if bbox:
            content_height = bbox[3] - bbox[1]
            canvas_height = self.canvas.winfo_height()
            if content_height <= canvas_height:
                self.canvas.yview_moveto(0)


    def open_settings(self):
        SettingsWindow(self.app)


    def save_settings(self):
        from core.settings import save_settings

        self.settings["distortion_on"] = self.app_state.distortion_on
        self.settings["saturation_on"] = self.app_state.saturation_on
        self.settings["bass_on"] = self.app_state.bass_on
        self.settings["noise_gate_on"] = self.app_state.noise_gate_on
        self.settings["distortion"] = self.app_state.distortion
        self.settings["saturation"] = self.app_state.saturation
        self.settings["bass_gain"] = self.app_state.bass_gain
        self.settings["noise_gate_threshold"] = self.app_state.noise_gate_threshold
        self.settings["volume"] = self.app_state.volume
        self.settings["volume_fx_on"] = self.app_state.volume_fx_on
        self.settings["volume_fx_off"] = self.app_state.volume_fx_off
        self.settings["monitor_volume"] = self.app_state.monitor_volume
        self.settings["fx_master_on"] = self.app_state.fx_master_on
        self.settings["monitor_on"] = self.app_state.monitor_on

        self.settings["window_width"] = self.root.winfo_width()
        self.settings["window_height"] = self.root.winfo_height()
        self.settings["window_x"] = self.root.winfo_x()
        self.settings["window_y"] = self.root.winfo_y()

        save_settings(self.settings)


    def refresh_loop(self):
        if self.meter:
            self.meter.draw()
        self.update_icons()
        self.root.after(30, self.refresh_loop)


    def on_close(self):
        self.save_settings()
        self.app.stream_manager.stop()
        self.root.destroy()


    def run(self):
        self.root.mainloop()

    def show_app_loading_screen(
        self,
        title_text="Wczytywanie...",
        status_text="Przygotowanie interfejsu...",
        show_cancel=False,
    ):
        self._active_loading_screen = self.app_loading_screen
        self.app_loading_screen.show(
            title_text=title_text,
            status_text=status_text,
            show_cancel=show_cancel,
        )

    def show_loading_screen(
        self,
        title_text="Pobieranie aktualizacji",
        status_text="Wczytywanie...",
        show_cancel=True,
    ):
        self._active_loading_screen = self.update_loading_screen
        self.update_loading_screen.show(
            title_text=title_text,
            status_text=status_text,
            show_cancel=show_cancel,
        )

    def _get_active_loading_screen(self):
        return self._active_loading_screen

    def set_loading_cancel_callback(self, callback):
        screen = self._get_active_loading_screen()
        if screen:
            screen.set_loading_cancel_callback(callback)

    def set_loading_cancel_enabled(self, enabled):
        screen = self._get_active_loading_screen()
        if screen:
            screen.set_loading_cancel_enabled(enabled)

    def set_loading_cancel_visible(self, visible):
        screen = self._get_active_loading_screen()
        if screen:
            screen.set_loading_cancel_visible(visible)

    def set_loading_progress(self, percent, status_text=None, smooth=True):
        screen = self._get_active_loading_screen()
        if screen:
            screen.set_loading_progress(percent, status_text=status_text, smooth=smooth)

    def set_loading_status(self, status_text):
        screen = self._get_active_loading_screen()
        if screen:
            screen.set_loading_status(status_text)

    def set_loading_indeterminate(self, enabled, status_text=None):
        screen = self._get_active_loading_screen()
        if screen:
            screen.set_loading_indeterminate(enabled, status_text=status_text)

    def apply_theme(self, theme_name):
        self.theme = get_theme(theme_name)
        self.root.configure(bg=self.theme["bg_root"])
        self.container.config(bg=self.theme["bg_root"])
        self.canvas.config(bg=self.theme["bg_root"])
        self.main_frame.config(bg=self.theme["bg_root"])
        if hasattr(self, "mic_icon"):
            self.mic_icon.config(bg=self.theme["bg_root"])
        if hasattr(self, "monitor_icon"):
            self.monitor_icon.config(bg=self.theme["bg_root"])
        if hasattr(self, "scrollbar"):
            self.scrollbar.base_color = self.theme["scrollbar_thumb"]
            try:
                self.scrollbar.redraw(*self.canvas.yview())
            except Exception:
                pass
        for slider in self.sliders:
            if hasattr(slider, "set_theme"):
                slider.set_theme(self.theme)
        if self.meter and hasattr(self.meter, "set_theme"):
            self.meter.set_theme(self.theme)
        self.app_loading_screen.apply_theme(self.theme)
        self.update_loading_screen.apply_theme(self.theme)
        self.update_icons()

    def hide_loading_screen(self):
        if self._active_loading_screen:
            self._active_loading_screen.hide()
            self._active_loading_screen = None
        else:
            self.app_loading_screen.hide()
            self.update_loading_screen.hide()
