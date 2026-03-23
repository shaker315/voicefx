import tkinter as tk


class MasterMeter(tk.Canvas):
    def __init__(self, parent, state, theme=None, save_callback=None, show_gate_toggle=True):
        self.theme = theme or {}
        self._apply_theme_defaults()
        self.save_callback = save_callback
        self.show_gate_toggle = show_gate_toggle
        super().__init__(
            parent,
            height=34,
            bg=self._c("meter_canvas_bg"),
            highlightthickness=0,
        )
        self.state = state
        self._dragging_gate = False
        self._dot_hitbox = None
        self._track_bounds = None
        self._gate_line_x = None

        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)

    def draw(self):
        self.delete("all")
        width = self.winfo_width()
        if width <= 2:
            return
        height = self.winfo_height()

        level = min(1.0, self.state.smoothed_rms * 7.0)
        fill_ratio = max(0.0, min(1.0, level))

        if self.show_gate_toggle:
            left = 8
            right = width - 26
            track_left = left + 6
            track_right = right - 6
        else:
            left = 10
            right = width - 10
            track_left = left
            track_right = right
        center_y = height / 2
        line_height = 6

        track_width = max(1, track_right - track_left)
        fill_w = int(track_width * fill_ratio)
        self._track_bounds = (track_left, track_right, center_y, line_height)

        self.create_line(
            track_left,
            center_y,
            track_right,
            center_y,
            fill=self._c("meter_track"),
            width=line_height,
            capstyle="round",
        )

        lit_right = track_left + fill_w
        step = 2
        x = track_left
        while x < lit_right:
            ratio = (x - track_left) / max(1, track_width)
            color = self._gradient_color(ratio)
            x2 = min(x + step, lit_right)
            self.create_line(
                x,
                center_y,
                x2,
                center_y,
                fill=color,
                width=line_height,
                capstyle="round",
            )
            x += step

        if self.show_gate_toggle:
            dot_x = width - 12
            dot_y = center_y
            dot_color = self._c("accent") if self.state.noise_gate_on else self._c("danger")
            self.create_oval(
                dot_x - 4,
                dot_y - 4,
                dot_x + 4,
                dot_y + 4,
                fill=dot_color,
                outline="",
            )
            self._dot_hitbox = (dot_x - 8, dot_y - 8, dot_x + 8, dot_y + 8)
        else:
            self._dot_hitbox = None

        self._gate_line_x = None
        if hasattr(self.state, "noise_gate_on") and self.state.noise_gate_on:
            gate_level = min(1.0, max(0.0, float(self.state.noise_gate_threshold) * 7.0))
            gate_x = track_left + int(track_width * gate_level)
            gate_x = max(track_left, min(track_right, gate_x))
            self._gate_line_x = gate_x
            gate_stipple = self._c("meter_gate_stipple")

            self.create_rectangle(
                track_left,
                center_y - (line_height / 2),
                gate_x,
                center_y + (line_height / 2),
                fill=self._c("meter_gate_fill"),
                width=0,
                stipple=gate_stipple if gate_stipple else "",
            )
            self.create_line(
                gate_x,
                center_y - 8,
                gate_x,
                center_y + 8,
                fill=self._c("meter_gate_line"),
                width=1,
            )

    def _on_press(self, event):
        if self._dot_hitbox and self._in_box(event.x, event.y, self._dot_hitbox):
            self.state.noise_gate_on = not self.state.noise_gate_on
            self._dragging_gate = False
            self.draw()
            if self.save_callback:
                self.save_callback()
            return

        if not self.state.noise_gate_on or not self._track_bounds:
            return

        track_left, track_right, center_y, line_height = self._track_bounds
        if abs(event.y - center_y) <= 12 and track_left <= event.x <= track_right:
            self._dragging_gate = True
            self._set_gate_from_x(event.x)

    def _on_drag(self, event):
        if not self._dragging_gate or not self.state.noise_gate_on:
            return
        self._set_gate_from_x(event.x)

    def _on_release(self, event):
        self._dragging_gate = False

    def _on_motion(self, event):
        is_over_dot = self._dot_hitbox and self._in_box(event.x, event.y, self._dot_hitbox)
        self.config(cursor="hand2" if is_over_dot else "arrow")

    def _on_leave(self, event):
        self.config(cursor="arrow")

    def _set_gate_from_x(self, x):
        if not self._track_bounds:
            return

        track_left, track_right, _center_y, _line_height = self._track_bounds
        min_ratio = 0.005 * 7.0
        max_ratio = 0.08 * 7.0

        min_x = track_left + (track_right - track_left) * min_ratio
        max_x = track_left + (track_right - track_left) * max_ratio
        clamped_x = max(min_x, min(max_x, x))
        ratio = (clamped_x - track_left) / max(1, (track_right - track_left))
        self.state.noise_gate_threshold = max(0.005, min(0.08, ratio / 7.0))
        self.draw()
        if self.save_callback:
            self.save_callback()

    def _in_box(self, x, y, box):
        x1, y1, x2, y2 = box
        return x1 <= x <= x2 and y1 <= y <= y2

    def _gradient_color(self, ratio):
        ratio = max(0.0, min(1.0, ratio))
        if ratio < 0.65:
            local = ratio / 0.65
            return self._blend("#1de782", "#ffd24a", local)
        if ratio < 0.88:
            local = (ratio - 0.65) / 0.23
            return self._blend("#ffd24a", "#ff9b2f", local)
        local = (ratio - 0.88) / 0.12
        return self._blend("#ff9b2f", "#7a1f3d", local)

    def _blend(self, start, end, amount):
        amount = max(0.0, min(1.0, amount))
        sr = int(start[1:3], 16)
        sg = int(start[3:5], 16)
        sb = int(start[5:7], 16)
        er = int(end[1:3], 16)
        eg = int(end[3:5], 16)
        eb = int(end[5:7], 16)

        r = int(sr + (er - sr) * amount)
        g = int(sg + (eg - sg) * amount)
        b = int(sb + (eb - sb) * amount)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _apply_theme_defaults(self):
        defaults = {
            "meter_bg": "#0a0a0f",
            "meter_canvas_bg": "#181824",
            "meter_border": "#1f2433",
            "meter_track": "#1a2130",
            "meter_tick": "#2e3548",
            "meter_text": "#8f99b3",
            "meter_gate_fill": "#101622",
            "meter_gate_line": "#6fa4ff",
            "meter_gate_text": "#6fa4ff",
            "meter_gate_stipple": "gray25",
        }
        for k, v in defaults.items():
            self.theme.setdefault(k, v)

    def _c(self, key):
        return self.theme.get(key)

    def set_theme(self, theme):
        self.theme = dict(theme or {})
        self._apply_theme_defaults()
        self.config(bg=self._c("meter_canvas_bg"))
        self.draw()
