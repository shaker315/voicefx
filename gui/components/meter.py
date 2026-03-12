import tkinter as tk


class MasterMeter(tk.Canvas):
    def __init__(self, parent, state):
        super().__init__(
            parent,
            height=58,
            bg="#0a0a0f",
            highlightthickness=0,
        )
        self.state = state

    def draw(self):
        self.delete("all")
        width = self.winfo_width()
        if width <= 2:
            return
        height = self.winfo_height()

        level = min(1.0, self.state.smoothed_rms * 7.0)
        fill_w = int(width * level)

        left = 8
        right = width - 8
        top = 18
        bottom = height - 16

        self.create_rectangle(left, top, right, bottom, fill="#141824", outline="#1f2433", width=1)

        for i in range(6):
            x = int(left + (right - left) * (i / 5))
            self.create_line(x, top - 5, x, top - 1, fill="#2e3548", width=1)

        inner_w = max(0, right - left - 2)
        lit = min(inner_w, fill_w)
        x = left + 1
        seg_w = 4
        gap = 1

        while x < left + 1 + lit:
            ratio = (x - (left + 1)) / max(1, inner_w)
            if ratio < 0.65:
                color = "#1de782"
            elif ratio < 0.88:
                color = "#ffb020"
            else:
                color = "#ff4c4c"

            x2 = min(x + seg_w, left + 1 + lit)
            self.create_rectangle(x, top + 2, x2, bottom - 2, fill=color, width=0)
            x += seg_w + gap

        if hasattr(self.state, "noise_gate_on") and self.state.noise_gate_on:
            gate_level = min(1.0, max(0.0, float(self.state.noise_gate_threshold) * 7.0))
            gate_x = left + 1 + int(inner_w * gate_level)
            gate_x = max(left + 1, min(right - 1, gate_x))

            self.create_rectangle(
                left + 1,
                top + 2,
                gate_x,
                bottom - 2,
                fill="#101622",
                width=0,
                stipple="gray25",
            )
            self.create_line(gate_x, top + 1, gate_x, bottom - 1, fill="#6fa4ff", width=1)
            self.create_text(
                gate_x,
                top - 8,
                text="BRAMKA",
                anchor="s",
                fill="#6fa4ff",
                font=("Segoe UI", 7, "bold"),
            )

        self.create_text(left, 10, text="WEJ", anchor="w", fill="#8f99b3", font=("Segoe UI", 8, "bold"))
        self.create_text(right, 10, text=f"{level * 100:>3.0f}%", anchor="e", fill="#8f99b3", font=("Segoe UI", 8))
