import tkinter as tk


class IconToggle(tk.Label):
    def __init__(self, parent, text, on_color, off_color, callback):
        super().__init__(
            parent,
            text=text,
            font=("Segoe UI", 30),
            bg="#0f0f14",
            cursor="hand2"
        )

        self.on_color = on_color
        self.off_color = off_color
        self.callback = callback
        self.active = True

        self.bind("<Button-1>", self.toggle)
        self.update_color()

    def toggle(self, event=None):
        self.active = not self.active
        self.update_color()
        if self.callback:
            self.callback(self.active)

    def update_color(self):
        self.config(fg=self.on_color if self.active else self.off_color)