import os
import math
import time
import tkinter as tk
import tkinter.font as tkfont

from gui.components.meter import MasterMeter
from gui.components.scrollbar_style import UltraThinScrollbar
from gui.components.slider import ModernSlider
from gui.components.tooltip import Tooltip
from gui.loading.loading_app_screen import AppLoadingScreen
from gui.loading.loading_update_screen import UpdateLoadingScreen
from gui.settings_window import SettingsWindow
from gui.theme import get_theme
from core.version import APP_VERSION


class MainWindow:
    def _resolve_icon_path(self, filename):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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

        self.root = tk.Tk()
        self.root.title("VOICE FX PRO")
        self.root.configure(bg=self.theme["bg_root"])
        self.root._voicefx_scroll_active_until = 0.0
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
        self.apply_theme(self.settings.get("theme", "dark"))

        self.root.bind("<Configure>", self.on_configure)
        self.refresh_loop()
        self.hide_loading_screen()

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

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill, outline="", tag=None, width=1):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=36,
            fill=fill,
            outline=outline,
            width=width,
            tags=tag,
        )

    def _create_rounded_section(self, parent, row, pady, sticky="ew", min_height=140, auto_fit=False):
        panel = tk.Canvas(
            parent,
            bg=self.theme["bg_root"],
            highlightthickness=0,
            bd=0,
            height=min_height,
        )
        panel.grid(row=row, column=0, sticky=sticky, padx=10, pady=pady)
        panel.grid_columnconfigure(0, weight=1)

        inner = tk.Frame(panel, bg=self.theme["bg_card"])
        window_id = panel.create_window((18, 18), window=inner, anchor="nw")

        def redraw(event=None):
            raw_width = panel.winfo_width() - 2
            raw_height = panel.winfo_height() - 2
            width = max(raw_width, 40)
            height = max(raw_height, 40)
            panel.delete("rounded_bg")
            self._draw_rounded_rect(
                panel,
                1,
                1,
                width,
                height,
                radius=24,
                fill=self.theme["bg_card"],
                outline=self.theme["card_border"],
                tag="rounded_bg",
                width=2,
            )
            panel.tag_lower("rounded_bg")
            panel.coords(window_id, 18, 18)
            panel.itemconfig(window_id, width=max(0, width - 36))
            if not auto_fit:
                panel.itemconfig(window_id, height=max(0, height - 36))

        def fit_height(event=None):
            if auto_fit:
                panel.configure(height=max(min_height, inner.winfo_reqheight() + 36))

        panel._redraw_card = redraw
        panel.bind("<Configure>", redraw)
        if auto_fit:
            inner.bind("<Configure>", fit_height)
        redraw()
        return panel, inner

    def _draw_badge_reset_icon(self, canvas, center_x, center_y, color):
        r = 5
        start = 35 + getattr(canvas, "_reset_angle", 0)
        extent = 290
        canvas.create_arc(
            center_x - r,
            center_y - r,
            center_x + r,
            center_y + r,
            start=start,
            extent=extent,
            style="arc",
            width=1.8,
            outline=color,
        )

        end_deg = start + extent
        theta = math.radians(end_deg)
        tip_x = center_x + r * math.cos(theta)
        tip_y = center_y - r * math.sin(theta)
        wing_len = 3.0
        left = theta + math.radians(155)
        right = theta - math.radians(155)

        lx = tip_x + wing_len * math.cos(left)
        ly = tip_y - wing_len * math.sin(left)
        rx = tip_x + wing_len * math.cos(right)
        ry = tip_y - wing_len * math.sin(right)

        canvas.create_line(tip_x, tip_y, lx, ly, fill=color, width=1.8)
        canvas.create_line(tip_x, tip_y, rx, ry, fill=color, width=1.8)

    def _create_section_badge(
        self,
        parent,
        text,
        width=130,
        height=34,
        action=None,
        tooltip_text=None,
        popup_action=None,
        popup_tooltip_text=None,
    ):
        badge = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=self.theme["bg_root"],
            highlightthickness=0,
            bd=0,
            cursor="arrow",
        )
        badge.display_text = text
        badge._text_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        badge._popup_action = popup_action
        badge._popup_tooltip_text = popup_tooltip_text or "Personalizacja"

        def redraw(event=None):
            badge.delete("all")
            current_width = max(40, badge.winfo_width() - 2)
            current_height = max(24, badge.winfo_height() - 2)
            radius = max(12, int(current_height / 2) - 1)
            self._draw_rounded_rect(
                badge,
                1,
                1,
                current_width,
                current_height,
                radius=radius,
                fill=self.theme["bg_card"],
                outline=self.theme["card_border"],
                tag="badge_bg",
                width=2,
            )
            text = badge.display_text
            popup_shift = 9 if badge._popup_action else 0
            text_x = (current_width / 2) - popup_shift
            badge.create_text(
                text_x,
                current_height / 2,
                text=text,
                fill=self.theme["fg_primary"],
                font=badge._text_font,
            )

            if badge._popup_action:
                text_width = badge._text_font.measure(text)
                popup_x = text_x + (text_width / 2) + 11
                popup_y = current_height / 2 + 1
                badge.create_text(
                    popup_x,
                    popup_y,
                    text="\u25be",
                    fill=self.theme["fg_primary"],
                    font=("Segoe UI", 9, "bold"),
                )
                badge.popup_center = (popup_x, popup_y)
            else:
                badge.popup_center = None
            if action:
                icon_x = current_width - 16
                icon_y = current_height / 2
                self._draw_badge_reset_icon(
                    badge,
                    icon_x,
                    icon_y,
                    getattr(badge, "_reset_color", self.theme["slider_reset"]),
                )
                badge.action_center = (icon_x, icon_y)
            else:
                badge.action_center = None

        badge._reset_angle = 0
        badge._reset_color = self.theme["slider_reset"]
        badge._reset_spin_after_id = None
        badge._reset_settle_after_id = None
        badge._reset_flash_after_id = None
        badge._redraw_badge = redraw
        badge._action = action
        badge._tooltip_text = tooltip_text or text
        badge._tooltip_window = None

        def show_badge_tooltip(event, text):
            if badge._tooltip_window or not text:
                return
            tw = tk.Toplevel(badge)
            tw.wm_overrideredirect(True)
            label = tk.Label(
                tw,
                text=text,
                background="#333333",
                foreground="white",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 10),
            )
            label.pack()
            badge._tooltip_window = tw
            move_badge_tooltip(event)

        def move_badge_tooltip(event):
            if badge._tooltip_window:
                x = event.x_root + 15
                y = event.y_root + 15
                badge._tooltip_window.wm_geometry(f"+{x}+{y}")

        def hide_badge_tooltip():
            if badge._tooltip_window:
                badge._tooltip_window.destroy()
                badge._tooltip_window = None

        def on_badge_click(event):
            if badge._action and badge.action_center:
                icon_x, icon_y = badge.action_center
                if abs(event.x - icon_x) <= 10 and abs(event.y - icon_y) <= 10:
                    badge._action()
                    return

            if badge._popup_action and badge.popup_center:
                popup_x, popup_y = badge.popup_center
                if abs(event.x - popup_x) <= 10 and abs(event.y - popup_y) <= 10:
                    badge._popup_action()
                    return

        def on_badge_motion(event):
            over_reset = False
            over_popup = False

            if badge._action and badge.action_center:
                icon_x, icon_y = badge.action_center
                over_reset = abs(event.x - icon_x) <= 10 and abs(event.y - icon_y) <= 10

            if badge._popup_action and badge.popup_center:
                popup_x, popup_y = badge.popup_center
                over_popup = abs(event.x - popup_x) <= 10 and abs(event.y - popup_y) <= 10

            if over_reset:
                badge.config(cursor="hand2")
                show_badge_tooltip(event, badge._tooltip_text)
                move_badge_tooltip(event)
            elif over_popup:
                badge.config(cursor="hand2")
                show_badge_tooltip(event, badge._popup_tooltip_text)
                move_badge_tooltip(event)
            else:
                badge.config(cursor="arrow")
                hide_badge_tooltip()

        badge.bind("<Configure>", redraw)
        badge.bind("<Button-1>", on_badge_click)
        badge.bind("<Motion>", on_badge_motion)
        badge.bind("<Leave>", lambda event: (badge.config(cursor="arrow"), hide_badge_tooltip()))
        redraw()
        return badge

    def _set_badge_text(self, badge, text):
        if not badge or not badge.winfo_exists():
            return
        badge.display_text = text
        if hasattr(badge, "_redraw_badge"):
            badge._redraw_badge()

    def _get_active_effects_count(self):
        effect_flags = (
            "distortion_on",
            "saturation_on",
            "bass_on",
            "shift_on",
            "bitcrusher_on",
            "exciter_on",
            "tube_on",
            "sub_bass_on",
            "echo_on",
        )
        return sum(1 for attr in effect_flags if getattr(self.app_state, attr, False))

    def _update_effects_badge_text(self):
        badge = getattr(self, "effects_badge", None)
        if not badge:
            return
        active_count = self._get_active_effects_count()
        text = "Efekty" if active_count <= 0 else f"Efekty {self._to_superscript(active_count)}"
        self._set_badge_text(badge, text)

    def _to_superscript(self, value):
        superscript = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")
        return str(value).translate(superscript)

    def _start_badge_reset_animation(self, badge):
        if not badge or not badge.winfo_exists():
            return
        for after_name in ("_reset_spin_after_id", "_reset_settle_after_id", "_reset_flash_after_id"):
            after_id = getattr(badge, after_name, None)
            if after_id is not None:
                try:
                    badge.after_cancel(after_id)
                except Exception:
                    pass
                setattr(badge, after_name, None)

        badge._reset_color = self.theme["slider_text_muted"]

        def animate():
            if not badge.winfo_exists():
                return
            badge._reset_angle = (badge._reset_angle + 20) % 360
            badge._redraw_badge()
            badge._reset_spin_after_id = badge.after(16, animate)

        animate()

    def _finish_badge_reset_animation(self, badge):
        if not badge or not badge.winfo_exists():
            return
        if badge._reset_spin_after_id is not None:
            try:
                badge.after_cancel(badge._reset_spin_after_id)
            except Exception:
                pass
            badge._reset_spin_after_id = None

        badge._reset_color = self.theme["accent"]
        start_angle = badge._reset_angle % 360
        delta = ((0 - start_angle + 180) % 360) - 180

        def settle(step=0, steps=8):
            if not badge.winfo_exists():
                return
            t = (step + 1) / steps
            eased = 1 - (1 - t) * (1 - t)
            badge._reset_angle = (start_angle + delta * eased) % 360
            badge._redraw_badge()
            if step + 1 < steps:
                badge._reset_settle_after_id = badge.after(16, settle, step + 1, steps)
            else:
                badge._reset_angle = 0
                badge._redraw_badge()
                badge._reset_settle_after_id = None

        def clear_flash():
            if not badge.winfo_exists():
                return
            badge._reset_angle = 0
            badge._reset_color = self.theme["slider_reset"]
            badge._redraw_badge()
            badge._reset_flash_after_id = None

        settle()
        badge._reset_flash_after_id = badge.after(420, clear_flash)

    def _get_popup_hint_color(self):
        return self.theme.get(
            "fg_secondary",
            self.theme.get("slider_text_muted", self.theme["fg_primary"]),
        )

    def _create_effect_visibility_row(self, parent, config, variable, on_toggle):
        row = tk.Frame(parent, bg=self.theme["bg_card"])
        row.pack(fill="x", padx=10, pady=2)

        cb = tk.Checkbutton(
            row,
            text=config["label"],
            variable=variable,
            command=on_toggle,
            bg=self.theme["bg_card"],
            fg=self.theme["fg_primary"],
            activebackground=self.theme["bg_card"],
            activeforeground=self.theme["fg_primary"],
            selectcolor=self.theme["bg_card"],
            highlightthickness=0,
            bd=0,
            font=("Segoe UI", 9),
            cursor="hand2",
        )
        cb.pack(anchor="w")
        return cb

    def _create_meter_section(self):
        self.meter_frame = tk.Frame(self.primary_list, bg=self.theme["bg_card"])
        self.meter_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 4))
        self.meter_frame.grid_columnconfigure(0, weight=1)

        self.meter_header = tk.Frame(self.meter_frame, bg=self.theme["bg_card"])
        self.meter_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(4, 0))
        self.meter_header.grid_columnconfigure(0, weight=1)

        self.meter_label = tk.Label(
            self.meter_header,
            text="Meter",
            bg=self.theme["bg_card"],
            fg=self.theme["slider_text"],
            font=("Segoe UI", 10, "bold"),
        )
        self.meter_label.grid(row=0, column=0, sticky="w")

        self.meter_toggle = tk.Canvas(
            self.meter_header,
            width=12,
            height=12,
            bg=self.theme["bg_card"],
            highlightthickness=0,
            cursor="hand2",
        )
        self.meter_toggle.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.meter_toggle.bind("<Button-1>", self._toggle_meter_gate)
        Tooltip(self.meter_toggle, "Bramka szumow")
        self._draw_meter_toggle()

        self.meter = MasterMeter(
            self.meter_frame,
            self.app_state,
            theme=self.theme,
            save_callback=self.save_settings,
            show_gate_toggle=False,
        )
        self.meter.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 4))

    def _draw_meter_toggle(self):
        if not hasattr(self, "meter_toggle") or not self.meter_toggle or not self.meter_toggle.winfo_exists():
            return
        self.meter_toggle.delete("all")
        color = self.theme["accent"] if self.app_state.noise_gate_on else self.theme["danger"]
        self.meter_toggle.create_oval(2, 2, 10, 10, fill=color, outline="")

    def _toggle_meter_gate(self, event=None):
        self.app_state.noise_gate_on = not self.app_state.noise_gate_on
        self._draw_meter_toggle()
        if self.meter and self.meter.winfo_exists():
            self.meter.draw()
        self.save_settings()

    def _get_visible_effect_configs(self):
        visible = [
            config
            for config in self.effect_slider_configs
            if self.settings.get(config["visibility_key"], True)
        ]
        return visible or [self.effect_slider_configs[0]]

    def _create_effect_slider(self, row, config):
        slider = ModernSlider(
            self.effects_list,
            config["label"],
            self.app_state,
            config["attr"],
            config["min_val"],
            config["max_val"],
            toggle_attr=config["toggle_attr"],
            save_callback=self.save_settings,
            default_value=config["default_value"],
            theme=self.theme,
        )
        slider.grid(row=row, column=0, sticky="ew", padx=10, pady=(6, 2) if row == 0 else 2)
        self.sliders.append(slider)
        self.effect_sliders.append(slider)
        return slider

    def _set_effect_visibility(self, config, is_visible):
        self.settings[config["visibility_key"]] = is_visible
        if not is_visible and config.get("toggle_attr"):
            setattr(self.app_state, config["toggle_attr"], False)

    def _get_primary_core_content_height(self):
        if not hasattr(self, "primary_list") or not self.primary_list.winfo_exists():
            return 130

        self.primary_list.update_idletasks()
        rows = []
        for row in (0, 1):
            widgets = self.primary_list.grid_slaves(row=row, column=0)
            if widgets:
                rows.append(widgets[0].winfo_reqheight())

        if not rows:
            return 130

        return sum(rows) + 48

    def _rebuild_effect_sliders(self):
        for slider in list(self.effect_sliders):
            if slider in self.sliders:
                self.sliders.remove(slider)
            try:
                slider.destroy()
            except Exception:
                pass
        self.effect_sliders = []

        visible_configs = self._get_visible_effect_configs()
        for row, config in enumerate(visible_configs):
            self._create_effect_slider(row, config)

        self._bind_scroll_targets()
        self.update_sections_layout()

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
        Tooltip(self.monitor_icon, "Odsluch")

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
        self.primary_section, self.primary_inner = self._create_rounded_section(
            self.main_frame, row=1, pady=(2, 0), min_height=210, auto_fit=False
        )
        self.primary_badge = self._create_section_badge(self.main_frame, "Glosnosc")
        self.primary_badge.place(in_=self.primary_section, relx=0.5, y=1, anchor="center")
        self.primary_inner.grid_columnconfigure(0, weight=1)
        self.primary_inner.grid_rowconfigure(0, weight=1)

        self.primary_scroll_host = tk.Frame(self.primary_inner, bg=self.theme["bg_card"])
        self.primary_scroll_host.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=(4, 4))
        self.primary_scroll_host.grid_columnconfigure(0, weight=1)
        self.primary_scroll_host.grid_rowconfigure(0, weight=1)
        self.primary_scroll_host.grid_propagate(False)

        self.primary_canvas = tk.Canvas(
            self.primary_scroll_host,
            bg=self.theme["bg_card"],
            highlightthickness=0,
            bd=0,
        )
        self.primary_canvas.grid(row=0, column=0, sticky="nsew")

        self.primary_scrollbar = UltraThinScrollbar(
            self.primary_scroll_host,
            target_canvas=self.primary_canvas,
            width=3,
            bg=self.theme["bg_card"],
            thumb_color=self.theme["scrollbar_thumb"],
            auto_hide_delay=1500,
        )

        self.primary_list = tk.Frame(self.primary_canvas, bg=self.theme["bg_card"])
        self.primary_window_id = self.primary_canvas.create_window((0, 0), window=self.primary_list, anchor="nw")
        self.primary_list.grid_columnconfigure(0, weight=1)
        self.primary_list.bind("<Configure>", self.update_primary_scrollregion)
        self.primary_canvas.bind("<Configure>", self.on_primary_canvas_configure)

        self.effects_section, self.effects_inner = self._create_rounded_section(
            self.main_frame, row=3, pady=(0, 4), sticky="nsew", min_height=220, auto_fit=False
        )
        self.effects_badge = self._create_section_badge(
            self.main_frame,
            "Efekty",
            width=138,
            action=self.reset_fx,
            tooltip_text="Reset efektow",
            popup_action=self.toggle_effects_customize_popup,
            popup_tooltip_text="Personalizacja",
        )
        self.effects_badge.place(in_=self.effects_section, relx=0.5, y=1, anchor="center")
        self._update_effects_badge_text()
        self.effects_inner.grid_columnconfigure(0, weight=1)
        self.effects_inner.grid_rowconfigure(0, weight=1)

        self.effects_scroll_host = tk.Frame(self.effects_inner, bg=self.theme["bg_card"])
        self.effects_scroll_host.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=(4, 4))
        self.effects_scroll_host.grid_columnconfigure(0, weight=1)
        self.effects_scroll_host.grid_rowconfigure(0, weight=1)
        self.effects_scroll_host.grid_propagate(False)

        self.effects_canvas = tk.Canvas(
            self.effects_scroll_host,
            bg=self.theme["bg_card"],
            highlightthickness=0,
            bd=0,
        )
        self.effects_canvas.grid(row=0, column=0, sticky="nsew")

        self.effects_scrollbar = UltraThinScrollbar(
            self.effects_scroll_host,
            target_canvas=self.effects_canvas,
            width=3,
            bg=self.theme["bg_card"],
            thumb_color=self.theme["scrollbar_thumb"],
            auto_hide_delay=1500,
        )

        self.effects_list = tk.Frame(self.effects_canvas, bg=self.theme["bg_card"])
        self.effects_window_id = self.effects_canvas.create_window((0, 0), window=self.effects_list, anchor="nw")
        self.effects_list.grid_columnconfigure(0, weight=1)
        self.effects_list.bind("<Configure>", self.update_effects_scrollregion)
        self.effects_canvas.bind("<Configure>", self.on_effects_canvas_configure)

        self.sliders = []

        slider = ModernSlider(
            self.primary_list,
            "Glosnosc mikrofonu",
            self.app_state,
            "volume",
            0.2,
            10.0,
            save_callback=self.save_settings,
            default_value=1,
            theme=self.theme,
        )
        slider.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 2))
        self.sliders.append(slider)

        slider = ModernSlider(
            self.primary_list,
            "Odsluch",
            self.app_state,
            "monitor_volume",
            0.05,
            2.0,
            save_callback=self.save_settings,
            default_value=1,
            theme=self.theme,
        )
        slider.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))
        self.sliders.append(slider)

        self._rebuild_effect_sliders()

        self._bind_scroll_targets()
        self.update_sections_layout()

    def toggle_effects_customize_popup(self):
        popup = self.effects_customize_popup
        if popup and popup.winfo_exists():
            self._close_effects_customize_popup()
            return
        self.open_effects_customize_popup()

    def _close_effects_customize_popup(self, event=None):
        popup = self.effects_customize_popup
        if popup and popup.winfo_exists():
            popup.destroy()
        self.effects_customize_popup = None

        if self._effects_customize_click_bind is not None:
            try:
                self.root.unbind("<Button-1>", self._effects_customize_click_bind)
            except Exception:
                pass
            self._effects_customize_click_bind = None

    def _on_root_click_close_customize(self, event):
        popup = self.effects_customize_popup
        if not popup or not popup.winfo_exists():
            self._close_effects_customize_popup()
            return

        try:
            px1 = popup.winfo_rootx()
            py1 = popup.winfo_rooty()
            px2 = px1 + popup.winfo_width()
            py2 = py1 + popup.winfo_height()

            bx1 = self.effects_badge.winfo_rootx()
            by1 = self.effects_badge.winfo_rooty()
            bx2 = bx1 + self.effects_badge.winfo_width()
            by2 = by1 + self.effects_badge.winfo_height()

            x = event.x_root
            y = event.y_root
        except tk.TclError:
            self._close_effects_customize_popup()
            return

        inside_popup = px1 <= x <= px2 and py1 <= y <= py2
        inside_button = bx1 <= x <= bx2 and by1 <= y <= by2

        if not inside_popup and not inside_button:
            self._close_effects_customize_popup()

    def open_effects_customize_popup(self):
        if self.effects_customize_popup and self.effects_customize_popup.winfo_exists():
            self._close_effects_customize_popup()

        popup = tk.Toplevel(self.root)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.transient(self.root)
        popup.configure(bg=self.theme["card_border"])
        self.effects_customize_popup = popup

        body = tk.Frame(popup, bg=self.theme["bg_card"])
        body.pack(fill="both", expand=True, padx=1, pady=1)

        title = tk.Label(
            body,
            text="Pokaz efekty",
            bg=self.theme["bg_card"],
            fg=self.theme["fg_primary"],
            font=("Segoe UI", 10, "bold"),
        )
        title.pack(anchor="w", padx=12, pady=(10, 4))

        vars_map = {}
        for config in self.effect_slider_configs:
            key = config["visibility_key"]
            var = tk.BooleanVar(value=self.settings.get(key, True))
            vars_map[key] = var

            def on_toggle(effect_config=config, variable=var):
                selected_count = sum(1 for value in vars_map.values() if value.get())
                if not variable.get() and selected_count == 0:
                    variable.set(True)
                    try:
                        self.root.bell()
                    except Exception:
                        pass
                    return

                self._set_effect_visibility(effect_config, variable.get())
                self.save_settings()
                self.update_icons()
                self._rebuild_effect_sliders()

            self._create_effect_visibility_row(body, config, var, on_toggle)

        popup.bind("<FocusOut>", self._close_effects_customize_popup)
        popup.bind("<Escape>", self._close_effects_customize_popup)

        self.root.update_idletasks()
        badge = self.effects_badge
        x = badge.winfo_rootx()
        y = badge.winfo_rooty() + badge.winfo_height() + 6
        popup.geometry(f"190x{82 + len(self.effect_slider_configs) * 28}+{x}+{y}")
        popup.deiconify()
        popup.lift()
        popup.focus_force()
        self._effects_customize_click_bind = self.root.bind("<Button-1>", self._on_root_click_close_customize, add="+")

    def create_meter(self):
        if self.settings.get("show_meter", True):
            self._create_meter_section()
            self._bind_scroll_targets()
        else:
            self.meter_frame = None
            self.meter_header = None
            self.meter_label = None
            self.meter_toggle = None
            self.meter = None

    def update_meter_visibility(self):
        if not self.root.winfo_exists():
            return
        if self.app_state.show_meter:
            if not hasattr(self, "meter") or self.meter is None:
                self._create_meter_section()
                self._bind_scroll_targets()
        else:
            if hasattr(self, "meter_frame") and self.meter_frame:
                self.meter_frame.destroy()
                self.meter_frame = None
                self.meter_header = None
                self.meter_label = None
                self.meter_toggle = None
            self.meter = None
        self._bind_scroll_targets()
        self.update_sections_layout()

    def refresh_scroll_bindings(self):
        self._bind_scroll_targets()
        self.update_sections_layout()

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
            available = self.main_frame.winfo_height() - top_height - gap_height - 22
            available = max(110, available)

            primary_content = self.primary_list.winfo_reqheight() + 36
            primary_core = max(92, self._get_primary_core_content_height())
            effects_content = self.effects_list.winfo_reqheight() + 36
            primary_min = 92
            effects_min = 92

            if available <= primary_core + effects_min:
                primary_height = max(primary_min, int(available * 0.58))
                effects_height = max(effects_min, available - primary_height)
            else:
                primary_height = primary_core
                remaining = max(0, available - primary_height)

                effects_priority = min(effects_content, 170)
                effects_height = max(effects_min, min(effects_priority, remaining))
                remaining = max(0, available - primary_height - effects_height)

                primary_extra = max(0, primary_content - primary_core)
                primary_growth = min(primary_extra, remaining)
                primary_height += primary_growth
                remaining -= primary_growth

                effects_height += remaining

            primary_height = max(primary_min, int(primary_height))
            effects_height = max(effects_min, int(effects_height))

            self._allow_primary_scroll = primary_height < primary_content - 1

            self.primary_section.configure(height=max(primary_min, primary_height))
            self.effects_section.configure(height=max(effects_min, effects_height))

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

    def reset_fx(self):
        badge = getattr(self, "effects_badge", None)
        effect_sliders = [slider for slider in self.sliders if getattr(slider, "toggle_attr", None)]

        def apply_reset():
            self.app_state.reset_fx()
            for slider in self.sliders:
                slider._intro_active = False
                slider.draw()
            self._finish_badge_reset_animation(badge)
            self._update_effects_badge_text()
            self.save_settings()

        if not effect_sliders:
            self._start_badge_reset_animation(badge)
            self.root.after(220, apply_reset)
            return

        self._start_badge_reset_animation(badge)
        for slider in effect_sliders[:-1]:
            slider.animate_reset()
        effect_sliders[-1].animate_reset(apply_callback=apply_reset)

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
        self.settings["noise_gate_on"] = self.app_state.noise_gate_on
        self.settings["distortion"] = self.app_state.distortion
        self.settings["saturation"] = self.app_state.saturation
        self.settings["bass_gain"] = self.app_state.bass_gain
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
        if self.meter and time.monotonic() >= self._scroll_active_until:
            self.meter.draw()
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
