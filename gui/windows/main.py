import os
import time
import tkinter as tk

from gui.components.tooltip import Tooltip
from gui.windows.loading import StartupSplash
from gui.windows.update import UpdateLoadingScreen
from gui.panels import EffectsPanel, VolumePanel
from gui.windows.settings import SettingsWindow
from gui.theme import get_theme
from core.version import APP_VERSION


class MainWindow:
    STARTUP_FIRST_STEP_DELAY_MS = 200
    STARTUP_STEP_DELAY_MS = 50

    def ensure_window_visible(self):
        try:
            self.root.attributes("-alpha", 1.0)
            self.root.deiconify()
            self.root.state("normal")
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def _resolve_icon_path(self, filename):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidates = [
            os.path.join(base_dir, "assets", "icons", filename),
            os.path.join(base_dir, "assets", filename),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]

    def __init__(self, app):
        self.app = app
        self.app_state = app.state
        self.settings = app.settings
        self.meter = None
        self.sliders = []
        self.effect_sliders = []
        self.effects_customize_popup = None
        self._effects_customize_click_bind = None
        self.effect_slider_configs = [
            {
                "label": "Przester",
                "attr": "distortion",
                "toggle_attr": "distortion_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_distortion",
            },
            {
                "label": "Saturacja",
                "attr": "saturation",
                "toggle_attr": "saturation_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_saturation",
            },
            {
                "label": "Podbicie basu",
                "attr": "bass_gain",
                "toggle_attr": "bass_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_bass",
            },
            {
                "label": "Megafon",
                "attr": "megafon",
                "toggle_attr": "megafon_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_megafon",
            },
            {
                "label": "Stare radio",
                "attr": "stare_radio",
                "toggle_attr": "stare_radio_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_stare_radio",
            },
            {
                "label": "Shift",
                "attr": "shift",
                "toggle_attr": "shift_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_shift",
            },
            {
                "label": "Bitcrusher",
                "attr": "bitcrusher",
                "toggle_attr": "bitcrusher_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_bitcrusher",
            },
            {
                "label": "Exciter",
                "attr": "exciter",
                "toggle_attr": "exciter_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_exciter",
            },
            {
                "label": "Tube",
                "attr": "tube",
                "toggle_attr": "tube_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_tube",
            },
            {
                "label": "Sub bass",
                "attr": "sub_bass",
                "toggle_attr": "sub_bass_on",
                "min_val": 1,
                "max_val": 10,
                "default_value": 1,
                "visibility_key": "show_effect_sub_bass",
            },
            {
                "label": "Echo",
                "attr": "echo",
                "toggle_attr": "echo_on",
                "min_val": 1,
                "max_val": 5,
                "default_value": 1,
                "visibility_key": "show_effect_echo",
            },
        ]
        self.theme = get_theme(self.settings.get("theme", "dark"))
        self._layout_syncing = False
        self._allow_primary_scroll = False
        self._primary_canvas_width = None
        self._effects_canvas_width = None
        self._scroll_active_until = 0.0
        self._startup_done = False
        self._startup_callback = None
        self.volume_panel = VolumePanel(self)
        self.effects_panel = EffectsPanel(self)

        self.root = tk.Tk()
        try:
            self.root.attributes("-alpha", 0.0)
        except Exception:
            pass
        self.root.title("VOICE FX PRO")
        self.root.configure(bg="#0f0f14")
        self.root._voicefx_scroll_active_until = 0.0
        self.root.withdraw()
        self._set_app_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app_loading_screen = StartupSplash(self.root, self.theme)
        self.update_loading_screen = UpdateLoadingScreen(self.root, self.theme)
        self._active_loading_screen = None

        self.setup_geometry()

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
        self.root.minsize(300, 300)

    def start_loading_ui(self, on_ready=None):
        self._startup_callback = on_ready
        self.show_app_loading_screen(show_cancel=False)
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            return
        self.root.after(self.STARTUP_FIRST_STEP_DELAY_MS, self._build_ui_step)

    def _build_ui_step(self, index=0):
        if not self.root.winfo_exists():
            return

        steps = [
            self.create_layout,
            self.create_top_bar,
            self.create_volume_sliders,
            self.create_effect_sliders,
            self.create_meter,
            lambda: self.apply_theme(self.settings.get("theme", "dark")),
            self._finalize_startup_ui,
        ]

        if index >= len(steps):
            return

        action = steps[index]
        self.show_app_loading_screen(show_cancel=False)
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            return

        action()
        if index < len(steps) - 1:
            self.show_app_loading_screen(show_cancel=False)
            try:
                self.root.update_idletasks()
                self.root.update()
            except tk.TclError:
                return
            self.root.after(self.STARTUP_STEP_DELAY_MS, lambda: self._build_ui_step(index + 1))

    def _finalize_startup_ui(self):
        self.root.bind("<Configure>", self.on_configure)
        self.refresh_loop()
        self.root.update_idletasks()
        self._startup_done = True
        self._finish_startup_after_delay()

    def _finish_startup_after_delay(self):
        self.hide_loading_screen()
        self.ensure_window_visible()
        if self._startup_callback:
            callback = self._startup_callback
            self._startup_callback = None
            self.root.after(1, callback)

    def _set_app_icon(self):
        try:
            ico_path = self._resolve_icon_path("icon.ico")
            png_path = self._resolve_icon_path("icon.png")

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

        self.main_frame = tk.Frame(self.container, bg=self.theme["bg_root"])
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, minsize=18, weight=0)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=0)

        self.section_gap = tk.Frame(self.main_frame, bg=self.theme["bg_root"], height=18)
        self.section_gap.grid(row=2, column=0, sticky="ew", padx=10)

        self.footer = tk.Frame(self.main_frame, bg=self.theme["bg_root"], height=16)
        self.footer.grid(row=4, column=0, sticky="ew", padx=5, pady=(0, 0))

        self.version_label = tk.Label(
            self.footer,
            text=f"v{APP_VERSION}",
            bg=self.theme["bg_root"],
            fg=self.theme["fg_muted"],
            font=("Segoe UI", 8),
        )
        self.version_label.pack(side="right", padx=(0, 2), pady=(0, 0))

    def on_configure(self, event):
        if not self.root.winfo_exists():
            return
        if not self._startup_done:
            return
        if self.root.state() == "iconic":
            if self.meter and self.meter.winfo_ismapped():
                self.meter.grid_remove()
        else:
            if self.meter and not self.meter.winfo_ismapped():
                self.meter.grid()
        self.update_sections_layout()

    def create_top_bar(self):
        self.top_bar = tk.Frame(self.main_frame, bg=self.theme["bg_root"], height=60)
        self.top_bar.grid(row=0, column=0, sticky="ew", pady=(8, 6), padx=10)
        self.top_bar.grid_columnconfigure(0, weight=1)
        self.top_bar.grid_columnconfigure(1, weight=1)
        self.top_bar.grid_columnconfigure(2, weight=1)

        self.mic_icon = tk.Label(
            self.top_bar,
            text="\U0001F3A4",
            font=("Segoe UI", 30),
            bg=self.theme["bg_root"],
            fg=self.theme["accent"] if self.app_state.fx_master_on else self.theme["danger"],
        )
        self.mic_icon.grid(row=0, column=0, sticky="w")
        self.mic_icon.config(cursor="hand2")
        self.mic_icon.bind("<Button-1>", self.toggle_mic_click)
        Tooltip(self.mic_icon, "Efekty")

        self.monitor_icon = tk.Label(
            self.top_bar,
            text="\U0001F3A7",
            font=("Segoe UI", 30),
            bg=self.theme["bg_root"],
            fg=self.theme["accent"] if self.app_state.monitor_on else self.theme["danger"],
        )
        self.monitor_icon.grid(row=0, column=2, sticky="e")
        self.monitor_icon.config(cursor="hand2")
        self.monitor_icon.bind("<Button-1>", self.toggle_monitor_click)
        Tooltip(self.monitor_icon, "Odsłuch")

        self.settings_btn = tk.Button(
            self.top_bar,
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
        self.settings_btn.grid(row=0, column=1)
        Tooltip(self.settings_btn, "Ustawienia")

    def create_sliders(self):
        self.sliders = []
        self.effect_sliders = []
        self.create_volume_sliders()
        self.create_effect_sliders()

        self._bind_scroll_targets()
        self.update_sections_layout()

    def create_volume_sliders(self):
        if hasattr(self, "primary_section") and self.primary_section and self.primary_section.winfo_exists():
            return
        self.volume_panel.build()

    def create_effect_sliders(self):
        if hasattr(self, "effects_section") and self.effects_section and self.effects_section.winfo_exists():
            return
        self.effects_panel.build()
        self._bind_scroll_targets()
        self.update_sections_layout()

    def create_meter(self):
        self.volume_panel.create_meter()

    def update_meter_visibility(self):
        self.volume_panel.update_meter_visibility()

    def refresh_scroll_bindings(self):
        self._bind_scroll_targets()
        self.update_sections_layout()

    def _draw_meter_toggle(self):
        self.volume_panel.draw_meter_toggle()

    def _get_primary_core_content_height(self):
        return self.volume_panel.get_primary_core_content_height()

    def _rebuild_effect_sliders(self):
        self.effects_panel.rebuild_sliders()

    def _update_effects_badge_text(self):
        self.effects_panel.update_badge_text()

    def toggle_effects_customize_popup(self):
        self.effects_panel.toggle_customize_popup()

    def _close_effects_customize_popup(self, event=None):
        self.effects_panel.close_customize_popup(event)

    def reset_fx(self):
        self.effects_panel.reset_fx()

    def on_primary_canvas_configure(self, event):
        if not hasattr(self, "primary_canvas") or not self.primary_canvas.winfo_exists():
            return
        new_width = max(0, int(event.width))
        if self._primary_canvas_width == new_width:
            self.update_primary_scrollregion()
            return
        self._primary_canvas_width = new_width
        try:
            self.primary_canvas.itemconfig(self.primary_window_id, width=new_width)
        except tk.TclError:
            return
        self.update_primary_scrollregion()

    def update_primary_scrollregion(self, event=None):
        if not hasattr(self, "primary_canvas") or not hasattr(self, "primary_list"):
            return
        try:
            self.primary_canvas.update_idletasks()
            content_height = self.primary_list.winfo_reqheight()
            content_width = self.primary_canvas.winfo_width()
            canvas_height = self.primary_canvas.winfo_height()
        except tk.TclError:
            return

        if content_width <= 1 or canvas_height <= 1:
            return

        self.primary_canvas.configure(scrollregion=(0, 0, content_width, content_height))

        needs_primary_scroll = self._allow_primary_scroll and content_height > canvas_height + 1

        if needs_primary_scroll:
            if self.primary_scrollbar.winfo_ismapped():
                self.primary_scrollbar.place_configure(y=2, height=max(0, canvas_height - 4))
            try:
                if self.primary_scrollbar.winfo_ismapped():
                    self.primary_scrollbar.redraw(*self.primary_canvas.yview())
            except Exception:
                pass
        else:
            if self.primary_scrollbar.winfo_ismapped():
                self.primary_scrollbar.hide_now()
            self.primary_canvas.yview_moveto(0)

    def on_effects_canvas_configure(self, event):
        if not hasattr(self, "effects_canvas") or not self.effects_canvas.winfo_exists():
            return
        new_width = max(0, int(event.width))
        if self._effects_canvas_width == new_width:
            self.update_effects_scrollregion()
            return
        self._effects_canvas_width = new_width
        try:
            self.effects_canvas.itemconfig(self.effects_window_id, width=new_width)
        except tk.TclError:
            return
        self.update_effects_scrollregion()

    def update_sections_layout(self):
        if self._layout_syncing:
            return
        if not hasattr(self, "main_frame") or not self.main_frame.winfo_exists():
            return
        if not hasattr(self, "primary_section") or not self.primary_section.winfo_exists():
            return
        if not hasattr(self, "effects_section") or not self.effects_section.winfo_exists():
            return

        self._layout_syncing = True
        try:
            self.main_frame.update_idletasks()

            top_height = self.top_bar.winfo_height() if hasattr(self, "top_bar") and self.top_bar.winfo_exists() else 60
            gap_height = self.section_gap.winfo_reqheight() if hasattr(self, "section_gap") and self.section_gap.winfo_exists() else 4
            primary_badge_overlap = int(getattr(self.primary_section, "_badge_overlap", 0) or 0)
            effects_badge_overlap = int(getattr(self.effects_section, "_badge_overlap", 0) or 0)


            available = self.main_frame.winfo_height() - top_height - gap_height - 22
            available -= (primary_badge_overlap + effects_badge_overlap)
            available = max(120, available)

            primary_content = self.primary_list.winfo_reqheight() + 36
            effects_content = self.effects_list.winfo_reqheight() + 36

            primary_core = max(96, self._get_primary_core_content_height())

            primary_soft_min = primary_core
            effects_soft_min = max(118, min(effects_content, 160))

            primary_hard_min = 84
            effects_hard_min = 98

            if available >= primary_soft_min + effects_soft_min:
                primary_height = primary_core
                effects_priority = min(effects_content, 170)
                effects_height = max(effects_soft_min, min(effects_priority, available - primary_height))
                remaining = max(0, available - primary_height - effects_height)

                if remaining > 0:
                    primary_extra = max(0, primary_content - primary_height)
                    grow_primary = min(primary_extra, remaining)
                    primary_height += grow_primary
                    remaining -= grow_primary
                if remaining > 0:
                    effects_height += min(max(0, effects_content - effects_height), remaining)
            else:
                primary_height = primary_soft_min
                effects_height = effects_soft_min
                deficit = (primary_height + effects_height) - available

                if deficit > 0:
                    reduce_effects = min(deficit, max(0, effects_height - effects_hard_min))
                    effects_height -= reduce_effects
                    deficit -= reduce_effects
                if deficit > 0:
                    reduce_primary = min(deficit, max(0, primary_height - primary_hard_min))
                    primary_height -= reduce_primary
                    deficit -= reduce_primary

                if deficit > 0:
                    total = max(1, primary_height + effects_height)
                    p_cut = int(deficit * (primary_height / total))
                    e_cut = deficit - p_cut
                    primary_height = max(64, primary_height - p_cut)
                    effects_height = max(72, effects_height - e_cut)

            primary_height = int(max(64, primary_height))
            effects_height = int(max(72, effects_height))

            self._allow_primary_scroll = (
                primary_height < (primary_content - 1)
                and effects_height <= (effects_soft_min + 1)
            )

            self.primary_section.configure(height=primary_height + primary_badge_overlap)
            self.effects_section.configure(height=effects_height + effects_badge_overlap)

            if hasattr(self.primary_section, "_redraw_card"):
                self.primary_section._redraw_card()
            if hasattr(self.effects_section, "_redraw_card"):
                self.effects_section._redraw_card()
            if hasattr(self, "primary_badge") and hasattr(self.primary_badge, "_redraw_badge"):
                self.primary_badge._redraw_badge()
            if hasattr(self, "effects_badge") and hasattr(self.effects_badge, "_redraw_badge"):
                self.effects_badge._redraw_badge()

            self.primary_inner.update_idletasks()
            self.effects_inner.update_idletasks()

            primary_available = self.primary_inner.winfo_height() - 12
            effects_available = self.effects_inner.winfo_height() - 12
            self.primary_scroll_host.configure(height=max(46, primary_available))
            self.effects_scroll_host.configure(height=max(46, effects_available))

            self.update_primary_scrollregion()
            self.update_effects_scrollregion()
        finally:
            self._layout_syncing = False

    def update_effects_scrollregion(self, event=None):
        if not hasattr(self, "effects_canvas") or not hasattr(self, "effects_list"):
            return
        try:
            self.effects_canvas.update_idletasks()
            bbox = self.effects_canvas.bbox("all")
            content_width = self.effects_canvas.winfo_width()
            canvas_height = self.effects_canvas.winfo_height()
        except tk.TclError:
            return

        if content_width <= 1 or canvas_height <= 1 or not bbox:
            return

        content_height = max(0, bbox[3] - bbox[1])
        self.effects_canvas.configure(scrollregion=(0, 0, content_width, content_height))

        if content_height > canvas_height + 1:
            if self.effects_scrollbar.winfo_ismapped():
                self.effects_scrollbar.place_configure(y=2, height=max(0, canvas_height - 4))
            try:
                if self.effects_scrollbar.winfo_ismapped():
                    self.effects_scrollbar.redraw(*self.effects_canvas.yview())
            except Exception:
                pass
        else:
            if self.effects_scrollbar.winfo_ismapped():
                self.effects_scrollbar.hide_now()
            self.effects_canvas.yview_moveto(0)

    def _bind_mousewheel_recursive(self, widget, handler):
        if not widget or not widget.winfo_exists():
            return
        try:
            widget.bind("<MouseWheel>", handler)
        except tk.TclError:
            return
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child, handler)

    def _bind_scroll_targets(self):
        self._bind_mousewheel_recursive(self.primary_scroll_host, self._on_primary_mousewheel)
        self._bind_mousewheel_recursive(self.primary_canvas, self._on_primary_mousewheel)
        self._bind_mousewheel_recursive(self.primary_list, self._on_primary_mousewheel)
        self._bind_mousewheel_recursive(self.effects_scroll_host, self._on_effects_mousewheel)
        self._bind_mousewheel_recursive(self.effects_canvas, self._on_effects_mousewheel)
        self._bind_mousewheel_recursive(self.effects_list, self._on_effects_mousewheel)
        self._bind_mousewheel_recursive(self.effects_scrollbar, self._on_effects_mousewheel)

    def _on_primary_mousewheel(self, event):
        if not hasattr(self, "primary_canvas") or not self.primary_canvas.winfo_exists():
            return
        try:
            primary_bbox = self.primary_canvas.bbox("all")
            primary_content_height = 0 if not primary_bbox else max(0, primary_bbox[3] - primary_bbox[1])
            canvas_height = self.primary_canvas.winfo_height()
        except tk.TclError:
            return "break"

        if not self._allow_primary_scroll or primary_content_height <= canvas_height:
            return "break"

        try:
            self._mark_scroll_active()
            self.primary_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.primary_scrollbar.place(
                relx=1.0,
                x=0,
                y=2,
                height=max(0, self.primary_canvas.winfo_height() - 4),
                anchor="ne",
                width=8,
            )
            self.primary_scrollbar.redraw(*self.primary_canvas.yview())
            self.primary_scrollbar.fade_in()
        except tk.TclError:
            return "break"
        return "break"

    def _on_effects_mousewheel(self, event):
        if not hasattr(self, "effects_scroll_host") or not self.effects_scroll_host.winfo_exists():
            return
        try:
            bbox = self.effects_canvas.bbox("all")
            content_height = 0 if not bbox else max(0, bbox[3] - bbox[1])
            canvas_height = self.effects_canvas.winfo_height()
        except tk.TclError:
            return "break"

        if content_height <= canvas_height:
            return "break"

        try:
            self._mark_scroll_active()
            self.effects_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.effects_scrollbar.place(
                relx=1.0,
                x=0,
                y=2,
                height=max(0, self.effects_canvas.winfo_height() - 4),
                anchor="ne",
                width=8,
            )
            self.effects_scrollbar.redraw(*self.effects_canvas.yview())
            self.effects_scrollbar.fade_in()
        except tk.TclError:
            return "break"
        return "break"

    def _mark_scroll_active(self):
        self._scroll_active_until = time.monotonic() + 0.15
        self.root._voicefx_scroll_active_until = self._scroll_active_until

    def update_icons(self):
        state = self.app_state
        self._update_effects_badge_text()
        self._draw_meter_toggle()

        if state.true_mute_active:
            self.mic_icon.config(fg=self.theme["fg_muted"], cursor="arrow")
            self.monitor_icon.config(fg=self.theme["fg_muted"], cursor="arrow")
            for slider in self.sliders:
                slider.draw()
            return

        self.mic_icon.config(
            fg=self.theme["accent"] if state.fx_master_on else self.theme["danger"],
            cursor="hand2",
        )
        self.monitor_icon.config(
            fg=self.theme["accent"] if state.monitor_on else self.theme["danger"],
            cursor="hand2",
        )

        for slider in self.sliders:
            slider.draw()

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

    def open_settings(self):
        SettingsWindow(self.app)

    def save_settings(self):
        from core.settings import save_settings

        self._update_effects_badge_text()
        self.settings["distortion_on"] = self.app_state.distortion_on
        self.settings["saturation_on"] = self.app_state.saturation_on
        self.settings["bass_on"] = self.app_state.bass_on
        self.settings["shift_on"] = self.app_state.shift_on
        self.settings["bitcrusher_on"] = self.app_state.bitcrusher_on
        self.settings["exciter_on"] = self.app_state.exciter_on
        self.settings["tube_on"] = self.app_state.tube_on
        self.settings["sub_bass_on"] = self.app_state.sub_bass_on
        self.settings["echo_on"] = self.app_state.echo_on
        self.settings["megafon_on"] = self.app_state.megafon_on
        self.settings["stare_radio_on"] = self.app_state.stare_radio_on
        self.settings["noise_gate_on"] = self.app_state.noise_gate_on
        self.settings["distortion"] = self.app_state.distortion
        self.settings["saturation"] = self.app_state.saturation
        self.settings["bass_gain"] = self.app_state.bass_gain
        self.settings["megafon"] = self.app_state.megafon
        self.settings["stare_radio"] = self.app_state.stare_radio
        self.settings["shift"] = self.app_state.shift
        self.settings["bitcrusher"] = self.app_state.bitcrusher
        self.settings["exciter"] = self.app_state.exciter
        self.settings["tube"] = self.app_state.tube
        self.settings["sub_bass"] = self.app_state.sub_bass
        self.settings["echo"] = self.app_state.echo
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
        if not self.root.winfo_exists():
            return
        if self.meter and time.monotonic() >= self._scroll_active_until:
            self.meter.draw()
        self.root.after(30, self.refresh_loop)

    def on_close(self):
        self.save_settings()
        if self.app.stream_manager:
            try:
                self.app.stream_manager.stop()
            except Exception:
                pass
        self.root.destroy()

    def run(self, on_ready=None):
        self.root.after(1, lambda: self.start_loading_ui(on_ready=on_ready))
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

    def set_loading_details(self, downloaded_bytes, total_bytes, speed_bytes_per_sec):
        screen = self._get_active_loading_screen()
        if screen and hasattr(screen, "set_loading_details"):
            screen.set_loading_details(downloaded_bytes, total_bytes, speed_bytes_per_sec)

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
        self.main_frame.config(bg=self.theme["bg_root"])
        if hasattr(self, "section_gap"):
            self.section_gap.config(bg=self.theme["bg_root"])
        if hasattr(self, "footer"):
            self.footer.config(bg=self.theme["bg_root"])

        if hasattr(self, "top_bar"):
            self.top_bar.config(bg=self.theme["bg_root"])
        if hasattr(self, "version_label"):
            self.version_label.config(
                bg=self.theme["bg_root"],
                fg=self.theme["fg_muted"],
            )
        if hasattr(self, "mic_icon"):
            self.mic_icon.config(bg=self.theme["bg_root"])
        if hasattr(self, "monitor_icon"):
            self.monitor_icon.config(bg=self.theme["bg_root"])
        if hasattr(self, "settings_btn"):
            self.settings_btn.config(
                bg=self.theme["bg_root"],
                fg=self.theme["fg_primary"],
                activebackground=self.theme["bg_root"],
                activeforeground=self.theme["fg_primary"],
            )

        for panel_name, inner_name in (
            ("primary_section", "primary_inner"),
            ("effects_section", "effects_inner"),
        ):
            panel = getattr(self, panel_name, None)
            inner = getattr(self, inner_name, None)
            if panel:
                panel.config(bg=self.theme["bg_root"])
                if hasattr(panel, "_redraw_card"):
                    panel._redraw_card()
            if inner:
                inner.config(bg=self.theme["bg_card"])

        for badge_name in ("primary_badge", "effects_badge"):
            badge = getattr(self, badge_name, None)
            if badge:
                badge.config(bg=self.theme["bg_root"])
                badge._reset_color = self.theme["slider_reset"]
                if hasattr(badge, "_redraw_badge"):
                    badge._redraw_badge()

        if hasattr(self, "effects_scroll_host"):
            self.effects_scroll_host.config(bg=self.theme["bg_card"])
        if hasattr(self, "primary_scroll_host"):
            self.primary_scroll_host.config(bg=self.theme["bg_card"])
        if hasattr(self, "primary_canvas"):
            self.primary_canvas.config(bg=self.theme["bg_card"])
        if hasattr(self, "primary_list"):
            self.primary_list.config(bg=self.theme["bg_card"])
        if hasattr(self, "effects_canvas"):
            self.effects_canvas.config(bg=self.theme["bg_card"])
        if hasattr(self, "effects_list"):
            self.effects_list.config(bg=self.theme["bg_card"])
        if hasattr(self, "primary_scrollbar"):
            self.primary_scrollbar.set_theme(
                bg=self.theme["bg_card"],
                thumb_color=self.theme["scrollbar_thumb"],
            )
        if hasattr(self, "effects_scrollbar"):
            self.effects_scrollbar.set_theme(
                bg=self.theme["bg_card"],
                thumb_color=self.theme["scrollbar_thumb"],
            )

        for slider in self.sliders:
            if hasattr(slider, "set_theme"):
                slider.set_theme(self.theme)

        if self.meter and hasattr(self.meter, "set_theme"):
            self.meter.set_theme(self.theme)
        if hasattr(self, "meter_frame") and self.meter_frame:
            self.meter_frame.config(bg=self.theme["bg_card"])
        if hasattr(self, "meter_header") and self.meter_header:
            self.meter_header.config(bg=self.theme["bg_card"])
        if hasattr(self, "meter_label") and self.meter_label:
            self.meter_label.config(bg=self.theme["bg_card"], fg=self.theme["slider_text"])
        if hasattr(self, "meter_toggle") and self.meter_toggle:
            self.meter_toggle.config(bg=self.theme["bg_card"])
            self._draw_meter_toggle()

        self.app_loading_screen.apply_theme(self.theme)
        self.update_loading_screen.apply_theme(self.theme)
        self.update_icons()
        self.update_sections_layout()

    def hide_loading_screen(self):
        if self._active_loading_screen:
            self._active_loading_screen.hide()
            self._active_loading_screen = None
        else:
            self.app_loading_screen.hide()
            self.update_loading_screen.hide()


