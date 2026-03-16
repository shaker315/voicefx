import tkinter as tk


class UltraThinScrollbar(tk.Canvas):
    def __init__(self, parent, target_canvas,
                 width=6,
                 bg="#0f0f14",
                 thumb_color="#5a5a6a",
                 auto_hide_delay=1000,
                 fade_steps=10,
                 fade_interval=20):

        super().__init__(parent,
                         width=width,
                         highlightthickness=0,
                         bg=bg)

        self.target_canvas = target_canvas
        self.width_px = width
        self.base_color = thumb_color
        self.auto_hide_delay = auto_hide_delay
        self.fade_steps = fade_steps
        self.fade_interval = fade_interval

        self.visible = False
        self.hide_job = None
        self.fade_job = None

        self.thumb_parts = []

        self.target_canvas.configure(yscrollcommand=self.on_canvas_scroll)
        self.bind("<Configure>", lambda e: self.redraw())

        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)


    def on_canvas_scroll(self, first, last):
        self.redraw(float(first), float(last))
        self.fade_in()

    def redraw(self, first=None, last=None):
        self.delete("all")
        self.thumb_parts.clear()

        if first is None or last is None:
            return

        height = self.winfo_height()
        y1 = first * height
        y2 = last * height

        if y2 - y1 < 20:
            y2 = y1 + 20

        radius = self.width_px // 2

        top = self.create_oval(
            0, y1,
            self.width_px, y1 + self.width_px,
            fill=self.base_color,
            outline=""
        )

        middle = self.create_rectangle(
            0, y1 + radius,
            self.width_px, y2 - radius,
            fill=self.base_color,
            outline=""
        )

        bottom = self.create_oval(
            0, y2 - self.width_px,
            self.width_px, y2,
            fill=self.base_color,
            outline=""
        )

        self.thumb_parts = [top, middle, bottom]


    def start_drag(self, event):
        self.drag(event)

    def drag(self, event):
        height = self.winfo_height()
        fraction = event.y / height
        self.target_canvas.yview_moveto(fraction)


    def fade_in(self):
        if not self.visible:
            self.place(relx=1.0, x=4, rely=0, relheight=1.0, anchor="ne")
            self.visible = True

        if self.fade_job:
            self.after_cancel(self.fade_job)

        if self.hide_job:
            self.after_cancel(self.hide_job)

        self.set_opacity(1.0)
        self.hide_job = self.after(self.auto_hide_delay, self.fade_out)

    def fade_out(self):
        step = 0

        def animate():
            nonlocal step
            opacity = 1.0 - (step / self.fade_steps)
            self.set_opacity(opacity)

            if step < self.fade_steps:
                step += 1
                self.fade_job = self.after(self.fade_interval, animate)
            else:
                self.place_forget()
                self.visible = False

        animate()


    def set_opacity(self, opacity):
        r, g, b = self.winfo_rgb(self.base_color)
        r = int((r >> 8) * opacity)
        g = int((g >> 8) * opacity)
        b = int((b >> 8) * opacity)

        color = f"#{r:02x}{g:02x}{b:02x}"

        for part in self.thumb_parts:
            self.itemconfig(part, fill=color)

    def set_theme(self, bg=None, thumb_color=None):
        if bg is not None:
            self.configure(bg=bg)
        if thumb_color is not None:
            self.base_color = thumb_color
            try:
                self.redraw(*self.target_canvas.yview())
            except Exception:
                pass
