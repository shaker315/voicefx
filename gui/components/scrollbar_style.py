import tkinter as tk


class UltraThinScrollbar(tk.Canvas):
    def __init__(self, parent, target_canvas,
                 width=6,
                 hover_width=8,
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
        self.base_width_px = width
        self.hover_width_px = max(width, hover_width)
        self.width_px = width
        self.base_color = thumb_color
        self.auto_hide_delay = auto_hide_delay
        self.fade_steps = fade_steps
        self.fade_interval = fade_interval

        self.visible = False
        self.is_hovered = False
        self.is_dragging = False
        self.hide_job = None
        self.fade_job = None
        self.width_job = None

        self.thumb_parts = []
        self._thumb_top = 0
        self._thumb_bottom = 0
        self._drag_offset = 0
        self._current_opacity = 1.0
        self._current_width = float(width)

        self.target_canvas.configure(yscrollcommand=self.on_canvas_scroll)
        self.bind("<Configure>", lambda e: self.redraw())

        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)


    def on_canvas_scroll(self, first, last):
        self.redraw(float(first), float(last))

    def _apply_current_width(self, width=None):
        if width is None:
            width = self.hover_width_px if (self.is_hovered or self.is_dragging) else self.base_width_px
        width = max(self.base_width_px, float(width))
        self._current_width = width
        self.width_px = max(1, int(round(width)))
        try:
            self.configure(width=self.width_px)
            if self.visible:
                self.place_configure(width=self.width_px)
        except tk.TclError:
            return
        if self.thumb_parts:
            self.redraw(*self.target_canvas.yview())

    def _cancel_width_animation(self):
        if self.width_job:
            self.after_cancel(self.width_job)
            self.width_job = None

    def _animate_width_to(self, target_width):
        self._cancel_width_animation()
        start_width = self._current_width
        target_width = float(target_width)
        steps = 6
        interval = 16

        if abs(start_width - target_width) < 0.1:
            self._apply_current_width(target_width)
            return

        def animate(step=0):
            if not self.winfo_exists():
                self.width_job = None
                return
            t = (step + 1) / steps
            eased = 1 - (1 - t) * (1 - t)
            width = start_width + (target_width - start_width) * eased
            self._apply_current_width(width)
            if step + 1 < steps:
                self.width_job = self.after(interval, animate, step + 1)
            else:
                self._apply_current_width(target_width)
                self.width_job = None

        animate()

    def redraw(self, first=None, last=None):
        self.delete("all")
        self.thumb_parts.clear()

        if first is None or last is None:
            return

        height = self.winfo_height()
        y1 = first * height
        y2 = last * height

        if y2 - y1 < 20:
            min_thumb = 20
            if y1 + min_thumb > height:
                y1 = max(0, height - min_thumb)
                y2 = height
            else:
                y2 = y1 + min_thumb

        y1 = max(0, min(y1, height))
        y2 = max(y1, min(y2, height))
        self._thumb_top = y1
        self._thumb_bottom = y2

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
        self.is_dragging = True
        self.fade_in()
        thumb_height = max(1, self._thumb_bottom - self._thumb_top)
        if self._thumb_top <= event.y <= self._thumb_bottom:
            self._drag_offset = event.y - self._thumb_top
        else:
            self._drag_offset = thumb_height / 2
        self.drag(event)

    def drag(self, event):
        height = self.winfo_height()
        if height <= 0:
            return
        thumb_height = max(1, self._thumb_bottom - self._thumb_top)
        max_thumb_top = max(0, height - thumb_height)
        thumb_top = max(0, min(max_thumb_top, event.y - self._drag_offset))
        first, last = self.target_canvas.yview()
        visible_fraction = max(0.0, float(last) - float(first))
        max_first = max(0.0, 1.0 - visible_fraction)
        if max_thumb_top <= 0 or max_first <= 0:
            fraction = 0.0
        else:
            fraction = (thumb_top / max_thumb_top) * max_first
        self.target_canvas.yview_moveto(fraction)

    def stop_drag(self, event=None):
        self.is_dragging = False
        target_width = self.hover_width_px if self.is_hovered else self.base_width_px
        self._animate_width_to(target_width)
        if not self.is_hovered:
            self._schedule_hide()

    def on_enter(self, event=None):
        self.is_hovered = True
        self.fade_in()
        self._animate_width_to(self.hover_width_px)

    def on_leave(self, event=None):
        self.is_hovered = False
        if not self.is_dragging:
            self._animate_width_to(self.base_width_px)
        if not self.is_dragging:
            self._schedule_hide()

    def fade_in(self):
        if not self.visible:
            height = max(0, self.target_canvas.winfo_height() - 4)
            self.place(relx=1.0, x=0, y=2, height=height, anchor="ne", width=self.width_px)
            self.visible = True

        if self.fade_job:
            self.after_cancel(self.fade_job)
            self.fade_job = None

        if self.hide_job:
            self.after_cancel(self.hide_job)
            self.hide_job = None

        target_width = self.hover_width_px if (self.is_hovered or self.is_dragging) else self.base_width_px
        self._animate_width_to(target_width)
        self.set_opacity(1.0)
        self._schedule_hide()

    def _schedule_hide(self):
        if self.hide_job:
            self.after_cancel(self.hide_job)
            self.hide_job = None
        if self.is_hovered or self.is_dragging:
            return
        self.hide_job = self.after(self.auto_hide_delay, self.fade_out)

    def fade_out(self):
        if self.is_hovered or self.is_dragging:
            self.hide_job = None
            return
        step = 0

        def animate():
            nonlocal step
            if self.is_hovered or self.is_dragging:
                self.fade_job = None
                self.set_opacity(1.0)
                return
            opacity = 1.0 - (step / self.fade_steps)
            self.set_opacity(opacity)

            if step < self.fade_steps:
                step += 1
                self.fade_job = self.after(self.fade_interval, animate)
            else:
                self.place_forget()
                self.visible = False
                self.fade_job = None

        animate()

    def hide_now(self):
        if self.hide_job:
            self.after_cancel(self.hide_job)
            self.hide_job = None
        if self.fade_job:
            self.after_cancel(self.fade_job)
            self.fade_job = None
        self._cancel_width_animation()
        self.is_hovered = False
        self.is_dragging = False
        self.width_px = self.base_width_px
        self._current_width = float(self.base_width_px)
        self.configure(width=self.base_width_px)
        self.delete("all")
        self.thumb_parts.clear()
        self.place_forget()
        self.visible = False


    def set_opacity(self, opacity):
        self._current_opacity = opacity
        fr, fg, fb = self.winfo_rgb(self.base_color)
        br, bg, bb = self.winfo_rgb(self["bg"])
        fr = fr >> 8
        fg = fg >> 8
        fb = fb >> 8
        br = br >> 8
        bg = bg >> 8
        bb = bb >> 8

        r = int(br + (fr - br) * opacity)
        g = int(bg + (fg - bg) * opacity)
        b = int(bb + (fb - bb) * opacity)

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
