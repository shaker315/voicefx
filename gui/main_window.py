import os
import tkinter as tk
from gui.components.tooltip import Tooltip
from gui.components.slider import ModernSlider
from gui.components.meter import MasterMeter
from gui.settings_window import SettingsWindow
from gui.components.scrollbar_style import UltraThinScrollbar
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

        self.setup_geometry()
        self.show_loading_screen(
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

    def _show_loading_screen(self, title_text="Pobieranie aktualizacji", status_text="Wczytywanie..."):
        if hasattr(self, "_loading") and self._loading:
            self._loading_title.config(text=title_text)
            self._loading_status.config(text=status_text)
            return

        self._loading = tk.Frame(self.root, bg=self.theme["loading_bg"])
        self._loading.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._loading_title = tk.Label(
            self._loading,
            text=title_text,
            fg=self.theme["loading_text"],
            bg=self.theme["loading_bg"],
            font=("Segoe UI", 14, "bold"),
        )
        self._loading_title.place(relx=0.5, rely=0.42, anchor="center")

        self._loading_status = tk.Label(
            self._loading,
            text=status_text,
            fg=self.theme["loading_muted"],
            bg=self.theme["loading_bg"],
            font=("Segoe UI", 10),
        )
        self._loading_status.place(relx=0.5, rely=0.49, anchor="center")

        bar_width = 320
        bar_height = 18
        self._loading_bar = tk.Canvas(
            self._loading,
            width=bar_width,
            height=bar_height,
            bg=self.theme["loading_bg"],
            highlightthickness=0,
        )
        self._loading_bar.place(relx=0.5, rely=0.58, anchor="center")

        self._loading_bar_bg = self._loading_bar.create_rectangle(
            0,
            0,
            bar_width,
            bar_height,
            fill=self.theme["loading_bar_bg"],
            outline="",
        )
        self._loading_bar_fill = self._loading_bar.create_rectangle(
            0,
            0,
            0,
            bar_height,
            fill=self.theme["loading_bar_fill"],
            outline="",
        )

        self._loading_percent = tk.Label(
            self._loading,
            text="0%",
            fg=self.theme["loading_text"],
            bg=self.theme["loading_bg"],
            font=("Segoe UI", 11, "bold"),
        )
        self._loading_percent.place(relx=0.5, rely=0.66, anchor="center")
        self._loading_cancel_btn = tk.Button(
            self._loading,
            text="Anuluj",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme["button_bg"],
            fg=self.theme["button_text"],
            activebackground=self.theme["button_bg_hover"],
            activeforeground=self.theme["button_text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            takefocus=0,
            cursor="hand2",
            command=self._on_loading_cancel,
        )
        self._loading_cancel_btn.place(relx=0.5, rely=0.76, anchor="center")
        self._loading_cancel_cb = None
        self._loading_target = 0
        self._loading_current = 0
        self._loading_anim_after = None
        self._loading_indeterminate = False
        self._loading_indeterminate_after = None
        self._loading_indeterminate_pos = 0

    def _hide_loading_screen(self):
        if hasattr(self, "_loading") and self._loading:
            self._loading.destroy()
            self._loading = None

    def _on_loading_cancel(self):
        if self._loading_cancel_cb:
            self._loading_cancel_cb()

    def set_loading_cancel_callback(self, callback):
        self._loading_cancel_cb = callback

    def set_loading_cancel_enabled(self, enabled):
        if hasattr(self, "_loading_cancel_btn"):
            state = "normal" if enabled else "disabled"
            self._loading_cancel_btn.config(state=state)

    def set_loading_cancel_visible(self, visible):
        if not hasattr(self, "_loading_cancel_btn"):
            return
        if visible:
            self._loading_cancel_btn.place(relx=0.5, rely=0.76, anchor="center")
        else:
            self._loading_cancel_btn.place_forget()

    def _apply_loading_progress(self, value):
        bar_width = int(self._loading_bar.cget("width"))
        fill_width = int(bar_width * (value / 100))
        self._loading_bar.coords(
            self._loading_bar_fill,
            0,
            0,
            fill_width,
            int(self._loading_bar.cget("height")),
        )
        self._loading_percent.config(text=f"{int(value)}%")

    def _loading_anim_step(self):
        if not hasattr(self, "_loading") or not self._loading:
            self._loading_anim_after = None
            return

        target = int(self._loading_target)
        current = int(self._loading_current)
        if current == target:
            self._loading_anim_after = None
            return

        delta = target - current
        step = max(1, int(abs(delta) * 0.25))
        if delta < 0:
            step = -step
        new_value = current + step
        if (step > 0 and new_value > target) or (step < 0 and new_value < target):
            new_value = target

        self._loading_current = new_value
        self._apply_loading_progress(new_value)

        self._loading_anim_after = self.root.after(30, self._loading_anim_step)

    def _loading_indeterminate_step(self):
        if not hasattr(self, "_loading") or not self._loading or not self._loading_indeterminate:
            self._loading_indeterminate_after = None
            return

        bar_width = int(self._loading_bar.cget("width"))
        bar_height = int(self._loading_bar.cget("height"))
        block_width = max(40, int(bar_width * 0.25))
        speed = max(4, int(bar_width * 0.02))

        self._loading_indeterminate_pos += speed
        if self._loading_indeterminate_pos > bar_width + block_width:
            self._loading_indeterminate_pos = -block_width

        x0 = self._loading_indeterminate_pos
        x1 = x0 + block_width
        self._loading_bar.coords(self._loading_bar_fill, x0, 0, x1, bar_height)
        self._loading_indeterminate_after = self.root.after(30, self._loading_indeterminate_step)

    def set_loading_progress(self, percent, status_text=None, smooth=True):
        if not hasattr(self, "_loading") or not self._loading:
            return

        if self._loading_indeterminate:
            self.set_loading_indeterminate(False)

        value = max(0, min(100, int(percent)))
        self._loading_target = value

        if not smooth:
            self._loading_current = value
            self._apply_loading_progress(value)
        elif self._loading_anim_after is None:
            self._loading_anim_after = self.root.after(0, self._loading_anim_step)

        if status_text is not None:
            self._loading_status.config(text=status_text)

    def set_loading_status(self, status_text):
        if hasattr(self, "_loading") and self._loading:
            self._loading_status.config(text=status_text)

    def set_loading_indeterminate(self, enabled, status_text=None):
        if not hasattr(self, "_loading") or not self._loading:
            return

        self._loading_indeterminate = bool(enabled)
        if status_text is not None:
            self._loading_status.config(text=status_text)

        if self._loading_indeterminate:
            self._loading_indeterminate_pos = -40
            if self._loading_indeterminate_after is None:
                self._loading_indeterminate_after = self.root.after(0, self._loading_indeterminate_step)
            self._loading_percent.config(text="...")
        else:
            if self._loading_indeterminate_after is not None:
                try:
                    self.root.after_cancel(self._loading_indeterminate_after)
                except Exception:
                    pass
                self._loading_indeterminate_after = None
            self._apply_loading_progress(self._loading_current)

    def show_loading_screen(
        self,
        title_text="Pobieranie aktualizacji",
        status_text="Wczytywanie...",
        show_cancel=False,
    ):
        self._show_loading_screen(title_text=title_text, status_text=status_text)
        self.set_loading_cancel_visible(show_cancel)
        if not show_cancel:
            self.set_loading_cancel_enabled(False)

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
        if hasattr(self, "_loading") and self._loading:
            self._hide_loading_screen()
            self._show_loading_screen()
        self.update_icons()

    def hide_loading_screen(self):
        self._hide_loading_screen()
