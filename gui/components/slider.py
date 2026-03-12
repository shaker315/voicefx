import math
import tkinter as tk
from gui.components.tooltip import Tooltip


class ModernSlider(tk.Frame):
    def __init__(
        self,
        parent,
        label,
        state,
        attr,
        min_val,
        max_val,
        toggle_attr=None,
        save_callback=None,
        default_value=1,
    ):
        super().__init__(parent, bg="#181824")

        self.state = state
        self.attr = attr
        self.toggle_attr = toggle_attr
        self.save_callback = save_callback
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.default_value = float(default_value)

        self.value = self.min_val
        self._intro_active = True
        self._display_min = self.min_val
        self._display_max = self.max_val

        self._reset_spin_after_id = None
        self._reset_settle_after_id = None
        self._reset_flash_after_id = None
        self._reset_in_progress = False
        self._reset_angle = 0
        self._reset_color = "#aaaaaa"

        self.columnconfigure(0, weight=1)

        top_row = tk.Frame(self, bg="#181824")
        top_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 0))
        top_row.columnconfigure(0, weight=1)

        self.label = tk.Label(
            top_row,
            text=label,
            bg="#181824",
            fg="white",
            font=("Segoe UI", 10, "bold"),
        )
        self.label.grid(row=0, column=0, sticky="w")

        self.reset_btn = tk.Canvas(
            top_row,
            width=16,
            height=16,
            bg="#181824",
            highlightthickness=0,
            cursor="hand2",
        )
        self.reset_btn.grid(row=0, column=2, padx=(4, 0))
        self.reset_btn.bind("<Button-1>", self.reset_single_fx)
        Tooltip(self.reset_btn, "Ustaw domyslnie")
        self._draw_reset_icon()

        if self.toggle_attr:
            self.toggle_indicator = tk.Canvas(
                top_row,
                width=12,
                height=12,
                bg="#181824",
                highlightthickness=0,
                cursor="hand2",
            )
            self.toggle_indicator.grid(row=0, column=1, padx=6)
            self.toggle_indicator.bind("<Button-1>", self.on_toggle_click)

        self.canvas = tk.Canvas(
            self,
            height=28,
            bg="#181824",
            highlightthickness=0,
        )
        self.canvas.grid(row=1, column=0, sticky="ew", padx=10, pady=4)

        self.canvas.bind("<Button-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<Configure>", lambda e: self.draw())

        self.value_label = tk.Label(
            self,
            text="0.00",
            bg="#181824",
            fg="#aaaaaa",
            font=("Segoe UI", 9),
        )
        self.value_label.grid(row=2, column=0, pady=(0, 6))

        self.draw()

    def _get_effective_bounds(self):
        min_val = self.min_val
        max_val = self.max_val

        if self.attr == "volume" and not self.state.fx_master_on:
            max_val = min(max_val, 2.0)

        return min_val, max_val

    def _draw_reset_icon(self):
        self.reset_btn.delete("all")

        cx, cy = 8, 8
        r = 5
        start = 35 + self._reset_angle
        extent = 290

        self.reset_btn.create_arc(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            start=start,
            extent=extent,
            style="arc",
            width=1.8,
            outline=self._reset_color,
        )

        end_deg = start + extent
        theta = math.radians(end_deg)
        tip_x = cx + r * math.cos(theta)
        tip_y = cy - r * math.sin(theta)

        wing_len = 3.2
        left = theta + math.radians(155)
        right = theta - math.radians(155)

        lx = tip_x + wing_len * math.cos(left)
        ly = tip_y - wing_len * math.sin(left)
        rx = tip_x + wing_len * math.cos(right)
        ry = tip_y - wing_len * math.sin(right)

        self.reset_btn.create_line(tip_x, tip_y, lx, ly, fill=self._reset_color, width=1.8)
        self.reset_btn.create_line(tip_x, tip_y, rx, ry, fill=self._reset_color, width=1.8)


    def draw(self):
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        if width < 10:
            self.after(10, self.draw)
            return

        track_height = 10
        fill_height = 5
        y = 14

        min_val, max_val = self._get_effective_bounds()
        target_value = float(getattr(self.state, self.attr, self.value))
        target_value = max(min_val, min(max_val, target_value))

        bounds_ease = 0.28
        self._display_min += (min_val - self._display_min) * bounds_ease
        self._display_max += (max_val - self._display_max) * bounds_ease
        if abs(min_val - self._display_min) < 0.001:
            self._display_min = min_val
        if abs(max_val - self._display_max) < 0.001:
            self._display_max = max_val

        ease = 0.20 if self._intro_active else 0.35
        self.value += (target_value - self.value) * ease
        if abs(target_value - self.value) < 0.01:
            self.value = target_value
            self._intro_active = False

        self.canvas.create_line(
            10,
            y,
            width - 10,
            y,
            fill="#2a2a38",
            width=track_height,
            capstyle="round",
        )

        visual_span = max(1e-6, (self._display_max - self._display_min))
        visual_value = max(self._display_min, min(self._display_max, self.value))
        percent = (visual_value - self._display_min) / visual_span
        percent = max(0.0, min(1.0, percent))
        fill_x = 10 + percent * (width - 20)

        if self.attr == "monitor_volume":
            color = "#00ff88" if self.state.monitor_on else "#444444"
        elif self.attr == "volume":
            color = "#444444" if self.state.true_mute_active else "#00ff88"
        else:
            if not self.state.fx_master_on:
                color = "#444444"
            elif self.toggle_attr and not getattr(self.state, self.toggle_attr, True):
                color = "#444444"
            else:
                color = "#00ff88"

        if self.attr == "monitor_volume" and not self.state.monitor_on:
            self.value_label.config(fg="#666666")
            self.label.config(fg="#666666")
        elif self.attr == "volume" and self.state.true_mute_active:
            self.value_label.config(fg="#666666")
            self.label.config(fg="#666666")
        elif self.toggle_attr and not getattr(self.state, self.toggle_attr, True):
            self.value_label.config(fg="#777777")
            self.label.config(fg="#777777")
        else:
            self.value_label.config(fg="#aaaaaa")
            self.label.config(fg="white")

        self.canvas.create_line(
            10,
            y,
            fill_x,
            y,
            fill=color,
            width=fill_height,
            capstyle="round",
        )

        self.canvas.create_oval(
            fill_x - 9,
            y - 9,
            fill_x + 9,
            y + 9,
            fill="#ffffff",
            outline="#222222",
            width=2,
        )

        self.value_label.config(text=f"{self.value:.2f}")

        if self.toggle_attr:
            self.draw_toggle_indicator()


    def set_value_from_x(self, x):
        if self.attr == "volume" and self.state.true_mute_active:
            return

        if self.attr == "monitor_volume" and not self.state.monitor_on:
            return

        if self.toggle_attr and not self.state.fx_master_on:
            return

        if self.toggle_attr and not getattr(self.state, self.toggle_attr, True):
            return

        width = self.canvas.winfo_width()
        if width <= 20:
            return

        percent = (x - 10) / (width - 20)
        percent = max(0, min(1, percent))

        min_val, max_val = self._get_effective_bounds()
        value = min_val + percent * (max_val - min_val)

        if self.attr == "volume" and hasattr(self.state, "set_volume"):
            self.state.set_volume(value)
            self.value = float(self.state.volume)
        else:
            setattr(self.state, self.attr, value)
            self.value = float(value)

        self._intro_active = False
        self.value_label.config(text=f"{self.value:.2f}")
        self.draw()

        if self.save_callback:
            self.save_callback()

    def click(self, event):
        self.set_value_from_x(event.x)

    def drag(self, event):
        self.set_value_from_x(event.x)


    def draw_toggle_indicator(self):
        self.toggle_indicator.delete("all")
        is_on = getattr(self.state, self.toggle_attr, False)
        color = "#00ff88" if is_on else "#ff4444"
        self.toggle_indicator.create_oval(2, 2, 10, 10, fill=color, outline="")

    def on_toggle_click(self, event=None):
        if not self.state.fx_master_on:
            return
        current = getattr(self.state, self.toggle_attr)
        setattr(self.state, self.toggle_attr, not current)
        self.draw()
        if self.save_callback:
            self.save_callback()


    def _animate_reset_spin(self):
        if not self._reset_in_progress:
            return

        self._reset_angle = (self._reset_angle + 20) % 360
        self._draw_reset_icon()
        self._reset_spin_after_id = self.after(16, self._animate_reset_spin)

    def _start_reset_animation(self):
        if self._reset_flash_after_id is not None:
            self.after_cancel(self._reset_flash_after_id)
            self._reset_flash_after_id = None

        if self._reset_settle_after_id is not None:
            self.after_cancel(self._reset_settle_after_id)
            self._reset_settle_after_id = None

        if self._reset_spin_after_id is not None:
            self.after_cancel(self._reset_spin_after_id)
            self._reset_spin_after_id = None

        self._reset_in_progress = True
        self._reset_color = "#c0c0c0"
        self._animate_reset_spin()

    def _settle_reset_icon(self, step=0, steps=8, start_angle=None, delta=None):
        if start_angle is None:
            start_angle = self._reset_angle % 360
            delta = ((0 - start_angle + 180) % 360) - 180

        t = (step + 1) / steps
        eased = 1 - (1 - t) * (1 - t)
        self._reset_angle = (start_angle + delta * eased) % 360
        self._draw_reset_icon()

        if step + 1 < steps:
            self._reset_settle_after_id = self.after(
                16, self._settle_reset_icon, step + 1, steps, start_angle, delta
            )
        else:
            self._reset_angle = 0
            self._draw_reset_icon()
            self._reset_settle_after_id = None

    def _finish_reset_animation(self):
        self._reset_in_progress = False

        if self._reset_spin_after_id is not None:
            self.after_cancel(self._reset_spin_after_id)
            self._reset_spin_after_id = None

        self._reset_color = "#00ff88"
        self._settle_reset_icon()

        def clear_flash():
            self._reset_angle = 0
            self._reset_color = "#aaaaaa"
            self._draw_reset_icon()

        self._reset_flash_after_id = self.after(420, clear_flash)

    def reset_single_fx(self, event=None):
        if self.attr == "volume" and self.state.true_mute_active:
            return
        if self._reset_in_progress:
            return

        self._start_reset_animation()

        def apply_reset():
            if self.attr == "volume" and hasattr(self.state, "set_volume"):
                self.state.set_volume(self.default_value)
            else:
                setattr(self.state, self.attr, self.default_value)

            self._intro_active = False
            self.draw()

            if self.save_callback:
                self.save_callback()

            self._finish_reset_animation()

        self.after(220, apply_reset)
