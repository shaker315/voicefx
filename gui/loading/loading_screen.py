import tkinter as tk


class LoadingScreen:
    def __init__(
        self,
        root,
        theme,
        default_title="Wczytywanie...",
        default_status="Przygotowanie...",
        default_show_cancel=False,
        show_progress_bar=True,
        show_progress_percent=True,
        show_download_details=False,
    ):
        self.root = root
        self.theme = theme
        self.default_title = default_title
        self.default_status = default_status
        self.default_show_cancel = default_show_cancel
        self.show_progress_bar = show_progress_bar
        self.show_progress_percent = show_progress_percent
        self.show_download_details = show_download_details

        self._loading = None
        self._loading_title = None
        self._loading_status = None
        self._loading_bar = None
        self._loading_bar_bg = None
        self._loading_bar_fill = None
        self._loading_percent = None
        self._loading_details = None
        self._loading_cancel_btn = None

        self._loading_cancel_cb = None
        self._loading_target = 0
        self._loading_current = 0
        self._loading_anim_after = None
        self._loading_indeterminate = False
        self._loading_indeterminate_after = None
        self._loading_indeterminate_pos = 0

    def show(self, title_text=None, status_text=None, show_cancel=None):
        title_text = self.default_title if title_text is None else title_text
        status_text = self.default_status if status_text is None else status_text
        show_cancel = self.default_show_cancel if show_cancel is None else show_cancel

        if self._loading:
            self._loading_title.config(text=title_text)
            self._loading_status.config(text=status_text)
            self.set_loading_cancel_visible(show_cancel)
            if not show_cancel:
                self.set_loading_cancel_enabled(False)
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

        if self.show_progress_bar:
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

        if self.show_progress_percent:
            self._loading_percent = tk.Label(
                self._loading,
                text="0%",
                fg=self.theme["loading_text"],
                bg=self.theme["loading_bg"],
                font=("Segoe UI", 11, "bold"),
            )
            self._loading_percent.place(relx=0.5, rely=0.66, anchor="center")

        if self.show_download_details:
            self._loading_details = tk.Label(
                self._loading,
                text="0 B / 0 B  |  0 B/s",
                fg=self.theme["loading_muted"],
                bg=self.theme["loading_bg"],
                font=("Segoe UI", 9),
            )
            self._loading_details.place(relx=0.5, rely=0.71, anchor="center")

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
        self.set_loading_cancel_visible(show_cancel)
        if not show_cancel:
            self.set_loading_cancel_enabled(False)

        self._loading_target = 0
        self._loading_current = 0
        self._loading_anim_after = None
        self._loading_indeterminate = False
        self._loading_indeterminate_after = None
        self._loading_indeterminate_pos = 0

    def hide(self):
        if self._loading:
            if self._loading_anim_after is not None:
                try:
                    self.root.after_cancel(self._loading_anim_after)
                except Exception:
                    pass
                self._loading_anim_after = None
            if self._loading_indeterminate_after is not None:
                try:
                    self.root.after_cancel(self._loading_indeterminate_after)
                except Exception:
                    pass
                self._loading_indeterminate_after = None
            self._loading.destroy()
            self._loading = None

    def _on_loading_cancel(self):
        if self._loading_cancel_cb:
            self._loading_cancel_cb()

    def set_loading_cancel_callback(self, callback):
        self._loading_cancel_cb = callback

    def set_loading_cancel_enabled(self, enabled):
        if self._loading_cancel_btn:
            state = "normal" if enabled else "disabled"
            self._loading_cancel_btn.config(state=state)

    def set_loading_cancel_visible(self, visible):
        if not self._loading_cancel_btn:
            return
        if visible:
            self._loading_cancel_btn.place(relx=0.5, rely=0.76, anchor="center")
        else:
            self._loading_cancel_btn.place_forget()

    def _apply_loading_progress(self, value):
        if not self._loading_bar or not self._loading_percent:
            if self._loading_percent:
                self._loading_percent.config(text=f"{int(value)}%")
            return
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
        if not self._loading:
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
        if not self._loading or not self._loading_indeterminate:
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
        if not self._loading:
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

    def set_loading_details(self, downloaded_bytes, total_bytes, speed_bytes_per_sec):
        if not self._loading or not self._loading_details:
            return
        downloaded_text = self._format_bytes(downloaded_bytes)
        total_text = self._format_bytes(total_bytes) if total_bytes > 0 else "?"
        speed_text = self._format_bytes(speed_bytes_per_sec) + "/s"
        self._loading_details.config(text=f"{downloaded_text} / {total_text}  |  {speed_text}")

    def set_loading_status(self, status_text):
        if self._loading:
            self._loading_status.config(text=status_text)

    def set_loading_indeterminate(self, enabled, status_text=None):
        if not self._loading:
            return

        self._loading_indeterminate = bool(enabled)
        if status_text is not None:
            self._loading_status.config(text=status_text)

        if self._loading_indeterminate:
            self._loading_indeterminate_pos = -40
            if self._loading_indeterminate_after is None:
                self._loading_indeterminate_after = self.root.after(0, self._loading_indeterminate_step)
            if self._loading_percent:
                self._loading_percent.config(text="...")
        else:
            if self._loading_indeterminate_after is not None:
                try:
                    self.root.after_cancel(self._loading_indeterminate_after)
                except Exception:
                    pass
                self._loading_indeterminate_after = None
            self._apply_loading_progress(self._loading_current)

    def apply_theme(self, theme):
        self.theme = theme
        if not self._loading:
            return

        self._loading.config(bg=self.theme["loading_bg"])
        self._loading_title.config(
            fg=self.theme["loading_text"],
            bg=self.theme["loading_bg"],
        )
        self._loading_status.config(
            fg=self.theme["loading_muted"],
            bg=self.theme["loading_bg"],
        )
        if self._loading_bar:
            self._loading_bar.config(bg=self.theme["loading_bg"])
            self._loading_bar.itemconfig(self._loading_bar_bg, fill=self.theme["loading_bar_bg"])
            self._loading_bar.itemconfig(self._loading_bar_fill, fill=self.theme["loading_bar_fill"])
        if self._loading_percent:
            self._loading_percent.config(
                fg=self.theme["loading_text"],
                bg=self.theme["loading_bg"],
            )
        if self._loading_details:
            self._loading_details.config(
                fg=self.theme["loading_muted"],
                bg=self.theme["loading_bg"],
            )
        self._loading_cancel_btn.config(
            bg=self.theme["button_bg"],
            fg=self.theme["button_text"],
            activebackground=self.theme["button_bg_hover"],
            activeforeground=self.theme["button_text"],
        )

    def _format_bytes(self, value):
        value = max(0, float(value))
        units = ["B", "KB", "MB", "GB"]
        idx = 0
        while value >= 1024 and idx < len(units) - 1:
            value /= 1024.0
            idx += 1
        if idx == 0:
            return f"{int(value)} {units[idx]}"
        return f"{value:.1f} {units[idx]}"
