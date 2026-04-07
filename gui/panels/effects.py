import tkinter as tk

from gui.components.scrollbar_style import UltraThinScrollbar
from gui.components.slider import ModernSlider
from .base import PanelBase


class EffectsPanel(PanelBase):
    def build(self):
        ui = self.ui
        ui.effects_section, ui.effects_inner = self.create_rounded_section(
            ui.main_frame, row=3, pady=(0, 4), sticky="nsew", min_height=220, auto_fit=False
        )
        ui.effects_badge = self.create_section_badge(
            ui.effects_section,
            "Efekty",
            width=138,
            action=ui.reset_fx,
            tooltip_text="Reset efektów",
            popup_action=ui.toggle_effects_customize_popup,
            popup_tooltip_text="Personalizacja",
        )
        self.update_badge_text()
        ui.effects_inner.grid_columnconfigure(0, weight=1)
        ui.effects_inner.grid_rowconfigure(0, weight=1)

        ui.effects_scroll_host = tk.Frame(ui.effects_inner, bg=ui.theme["bg_card"])
        ui.effects_scroll_host.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=(4, 4))
        ui.effects_scroll_host.grid_columnconfigure(0, weight=1)
        ui.effects_scroll_host.grid_rowconfigure(0, weight=1)
        ui.effects_scroll_host.grid_propagate(False)

        ui.effects_canvas = tk.Canvas(
            ui.effects_scroll_host,
            bg=ui.theme["bg_card"],
            highlightthickness=0,
            bd=0,
        )
        ui.effects_canvas.grid(row=0, column=0, sticky="nsew")

        ui.effects_scrollbar = UltraThinScrollbar(
            ui.effects_scroll_host,
            target_canvas=ui.effects_canvas,
            width=3,
            bg=ui.theme["bg_card"],
            thumb_color=ui.theme["scrollbar_thumb"],
            auto_hide_delay=1500,
        )

        ui.effects_list = tk.Frame(ui.effects_canvas, bg=ui.theme["bg_card"])
        ui.effects_window_id = ui.effects_canvas.create_window((0, 0), window=ui.effects_list, anchor="nw")
        ui.effects_list.grid_columnconfigure(0, weight=1)
        ui.effects_list.bind("<Configure>", ui.update_effects_scrollregion)
        ui.effects_canvas.bind("<Configure>", ui.on_effects_canvas_configure)
        self.rebuild_sliders()

    def get_visible_effect_configs(self):
        ui = self.ui
        visible = [
            config
            for config in ui.effect_slider_configs
            if ui.settings.get(config["visibility_key"], True)
        ]
        return visible or [ui.effect_slider_configs[0]]

    def create_effect_slider(self, row, config):
        ui = self.ui
        slider = ModernSlider(
            ui.effects_list,
            config["label"],
            ui.app_state,
            config["attr"],
            config["min_val"],
            config["max_val"],
            toggle_attr=config["toggle_attr"],
            save_callback=ui.save_settings,
            default_value=config["default_value"],
            theme=ui.theme,
        )
        slider.grid(row=row, column=0, sticky="ew", padx=10, pady=(6, 2) if row == 0 else 2)
        ui.sliders.append(slider)
        ui.effect_sliders.append(slider)
        return slider

    def set_effect_visibility(self, config, is_visible):
        ui = self.ui
        ui.settings[config["visibility_key"]] = is_visible
        if not is_visible and config.get("toggle_attr"):
            setattr(ui.app_state, config["toggle_attr"], False)

    def rebuild_sliders(self):
        ui = self.ui
        for slider in list(ui.effect_sliders):
            if slider in ui.sliders:
                ui.sliders.remove(slider)
            try:
                slider.destroy()
            except Exception:
                pass
        ui.effect_sliders = []

        visible_configs = self.get_visible_effect_configs()
        for row, config in enumerate(visible_configs):
            self.create_effect_slider(row, config)

        ui._bind_scroll_targets()
        ui.update_sections_layout()

    def get_active_effects_count(self):
        ui = self.ui
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
            "megafon_on",
            "stare_radio_on",
        )
        return sum(1 for attr in effect_flags if getattr(ui.app_state, attr, False))

    def to_superscript(self, value):
        superscript = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")
        return str(value).translate(superscript)

    def update_badge_text(self):
        badge = getattr(self.ui, "effects_badge", None)
        if not badge:
            return
        active_count = self.get_active_effects_count()
        text = "Efekty" if active_count <= 0 else f"Efekty {self.to_superscript(active_count)}"
        self.set_badge_text(badge, text)

    def start_badge_reset_animation(self, badge):
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

    def finish_badge_reset_animation(self, badge):
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

    def reset_fx(self):
        ui = self.ui
        badge = getattr(ui, "effects_badge", None)
        effect_sliders = [slider for slider in ui.sliders if getattr(slider, "toggle_attr", None)]

        def apply_reset():
            ui.app_state.reset_fx()
            for slider in ui.sliders:
                slider._intro_active = False
                slider.draw()
            self.finish_badge_reset_animation(badge)
            self.update_badge_text()
            ui.save_settings()

        if not effect_sliders:
            self.start_badge_reset_animation(badge)
            ui.root.after(220, apply_reset)
            return

        self.start_badge_reset_animation(badge)
        for slider in effect_sliders[:-1]:
            slider.animate_reset()
        effect_sliders[-1].animate_reset(apply_callback=apply_reset)

    def create_effect_visibility_row(self, parent, config, variable, on_toggle):
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

    def toggle_customize_popup(self):
        popup = self.ui.effects_customize_popup
        if popup and popup.winfo_exists():
            self.close_customize_popup()
            return
        self.open_customize_popup()

    def close_customize_popup(self, event=None):
        ui = self.ui
        popup = ui.effects_customize_popup
        if popup and popup.winfo_exists():
            popup.destroy()
        ui.effects_customize_popup = None

        if ui._effects_customize_click_bind is not None:
            try:
                ui.root.unbind("<Button-1>", ui._effects_customize_click_bind)
            except Exception:
                pass
            ui._effects_customize_click_bind = None

    def on_root_click_close_customize(self, event):
        ui = self.ui
        popup = ui.effects_customize_popup
        if not popup or not popup.winfo_exists():
            self.close_customize_popup()
            return

        try:
            px1 = popup.winfo_rootx()
            py1 = popup.winfo_rooty()
            px2 = px1 + popup.winfo_width()
            py2 = py1 + popup.winfo_height()

            bx1, by1, bx2, by2 = self.get_badge_screen_bounds(ui.effects_badge)

            x = event.x_root
            y = event.y_root
        except tk.TclError:
            self.close_customize_popup()
            return

        inside_popup = px1 <= x <= px2 and py1 <= y <= py2
        inside_button = bx1 <= x <= bx2 and by1 <= y <= by2
        if not inside_popup and not inside_button:
            self.close_customize_popup()

    def open_customize_popup(self):
        ui = self.ui
        if ui.effects_customize_popup and ui.effects_customize_popup.winfo_exists():
            self.close_customize_popup()

        popup = tk.Toplevel(ui.root)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.transient(ui.root)
        popup.configure(bg=ui.theme["card_border"])
        ui.effects_customize_popup = popup

        body = tk.Frame(popup, bg=ui.theme["bg_card"])
        body.pack(fill="both", expand=True, padx=1, pady=1)

        title = tk.Label(
            body,
            text="Pokaż efekty",
            bg=ui.theme["bg_card"],
            fg=ui.theme["fg_primary"],
            font=("Segoe UI", 10, "bold"),
        )
        title.pack(anchor="w", padx=12, pady=(10, 4))

        vars_map = {}
        for config in ui.effect_slider_configs:
            key = config["visibility_key"]
            var = tk.BooleanVar(value=ui.settings.get(key, True))
            vars_map[key] = var

            def on_toggle(effect_config=config, variable=var):
                selected_count = sum(1 for value in vars_map.values() if value.get())
                if not variable.get() and selected_count == 0:
                    variable.set(True)
                    try:
                        ui.root.bell()
                    except Exception:
                        pass
                    return

                self.set_effect_visibility(effect_config, variable.get())
                ui.save_settings()
                ui.update_icons()
                self.rebuild_sliders()

            self.create_effect_visibility_row(body, config, var, on_toggle)

        popup.bind("<FocusOut>", self.close_customize_popup)
        popup.bind("<Escape>", self.close_customize_popup)

        ui.root.update_idletasks()
        badge = ui.effects_badge
        bx1, by1, _bx2, by2 = self.get_badge_screen_bounds(badge)
        x = int(bx1)
        y = int(by2 + 6)
        popup.geometry(f"190x{82 + len(ui.effect_slider_configs) * 28}+{x}+{y}")
        popup.deiconify()
        popup.lift()
        popup.focus_force()
        ui._effects_customize_click_bind = ui.root.bind("<Button-1>", self.on_root_click_close_customize, add="+")
