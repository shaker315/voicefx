import os
import time
import threading
import tkinter as tk

try:
    from PIL import Image, ImageSequence, ImageTk
except Exception:
    Image = None
    ImageSequence = None
    ImageTk = None


class AppLoadingScreen:
    def __init__(self, root, theme):
        self.root = root
        self.theme = theme
        self._startup_bg = "#0f0f14"

        self._overlay = None
        self._gif_label = None

        self._tk_frames = []
        self._pil_frames = []
        self._frame_delays = []
        self._scaled_frames = []
        self._base_frames = []
        self._first_frame = None
        self._current_frame = 0
        self._anim_after = None

        self._hide_anim_after = None
        self._hide_progress = 0.0
        self._shown_at = 0.0
        self._hide_requested = False
        self._last_size_key = None
        self._load_thread = None

        self._gif_path = self._resolve_gif_path()
        self._first_frame = None

    def _resolve_gif_path(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_dir, "assets", "giphs", "loading_app.gif")

    def _load_frames_all(self):
        self._tk_frames = []
        self._pil_frames = []
        self._frame_delays = []

        if not os.path.exists(self._gif_path):
            return

        if Image is not None:
            try:
                img = Image.open(self._gif_path)
                frame_iter = ImageSequence.Iterator(img) if ImageSequence is not None else [img]
                for frame in frame_iter:
                    self._pil_frames.append(frame.copy().convert("RGBA"))
                    dur = int(frame.info.get("duration", img.info.get("duration", 45)))
                    self._frame_delays.append(max(16, min(200, dur)))
            except Exception:
                self._pil_frames = []
                self._frame_delays = []

        if len(self._pil_frames) > 1:
            return

        self._pil_frames = []
        self._frame_delays = []
        i = 0
        while True:
            try:
                frame = tk.PhotoImage(file=self._gif_path, format=f"gif -index {i}")
                self._tk_frames.append(frame)
                self._frame_delays.append(45)
                i += 1
            except Exception:
                break

    def _get_target_dimensions(self, src_w, src_h):
        if self._overlay and self._overlay.winfo_exists():
            w = self._overlay.winfo_width()
            h = self._overlay.winfo_height()
        else:
            self.root.update_idletasks()
            w = self.root.winfo_width()
            h = self.root.winfo_height()

        w = max(300, w)
        h = max(300, h)
        target_w = max(96, int(w * 0.62))
        target_h = max(96, int(h * 0.62))
        scale = max(0.15, min(target_w / max(1, src_w), target_h / max(1, src_h)))
        return max(1, int(round(src_w * scale))), max(1, int(round(src_h * scale)))

    def _load_first_frame_fast(self):
        if not os.path.exists(self._gif_path):
            return None

        if Image is not None and ImageTk is not None:
            try:
                img = Image.open(self._gif_path)
                frame = img.copy().convert("RGBA")
                out_w, out_h = self._get_target_dimensions(*frame.size)
                resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.LANCZOS)
                return ImageTk.PhotoImage(frame.resize((out_w, out_h), resample))
            except Exception:
                pass

        try:
            frame = tk.PhotoImage(file=self._gif_path, format="gif -index 0")
            out_w, out_h = self._get_target_dimensions(frame.width(), frame.height())
            if out_w == frame.width() and out_h == frame.height():
                return frame
            scale_x = out_w / max(1, frame.width())
            scale_y = out_h / max(1, frame.height())
            scale = min(scale_x, scale_y)
            if scale >= 1.0:
                zoom_n = max(1, int(scale + 0.999))
                return frame.zoom(zoom_n, zoom_n)
            sub_n = max(1, int(round(1.0 / max(scale, 0.01))))
            return frame.subsample(sub_n, sub_n)
        except Exception:
            return None

    def _build_scaled_frames(self):
        if (not self._tk_frames and not self._pil_frames) or not self._overlay or not self._overlay.winfo_exists():
            self._scaled_frames = []
            return

        w = max(1, self._overlay.winfo_width())
        h = max(1, self._overlay.winfo_height())
        size_key = (w, h)
        if size_key == self._last_size_key and self._scaled_frames:
            return
        self._last_size_key = size_key

        if self._pil_frames:
            bw, bh = self._pil_frames[0].size
        else:
            bw = max(1, self._tk_frames[0].width())
            bh = max(1, self._tk_frames[0].height())

        target_w = max(96, int(w * 0.62))
        target_h = max(96, int(h * 0.62))
        scale = max(0.15, min(target_w / bw, target_h / bh))

        if self._pil_frames and ImageTk is not None and Image is not None:
            out_w = max(1, int(round(bw * scale)))
            out_h = max(1, int(round(bh * scale)))
            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.LANCZOS)
            self._scaled_frames = [
                ImageTk.PhotoImage(frame.resize((out_w, out_h), resample))
                for frame in self._pil_frames
            ]
            return

        zoom_n = 1
        sub_n = 1
        if scale >= 1.0:
            zoom_n = max(1, int(scale + 0.999))
        else:
            sub_n = max(1, int(round(1.0 / scale)))

        out = []
        for frame in self._tk_frames:
            if sub_n > 1:
                out.append(frame.subsample(sub_n, sub_n))
            elif zoom_n > 1:
                out.append(frame.zoom(zoom_n, zoom_n))
            else:
                out.append(frame)
        self._scaled_frames = out

    def _build_base_frames(self):
        if self._pil_frames and ImageTk is not None:
            try:
                self._base_frames = [ImageTk.PhotoImage(frame) for frame in self._pil_frames]
                return
            except Exception:
                self._base_frames = []
        if self._tk_frames:
            self._base_frames = list(self._tk_frames)
        else:
            self._base_frames = []

    def _get_initial_frame(self):
        if self._pil_frames and ImageTk is not None:
            try:
                return ImageTk.PhotoImage(self._pil_frames[0])
            except Exception:
                return self._first_frame
        if self._tk_frames:
            return self._tk_frames[0]
        return self._first_frame

    def _on_overlay_configure(self, event=None):
        if not self._overlay or not self._overlay.winfo_exists():
            return
        if self._overlay.winfo_width() < 10 or self._overlay.winfo_height() < 10:
            return
        self._build_scaled_frames()
        active_frames = self._scaled_frames or self._base_frames
        if active_frames and self._gif_label and self._gif_label.winfo_exists():
            idx = min(self._current_frame, len(active_frames) - 1)
            self._gif_label.config(image=active_frames[idx], text="")
            self._gif_label.image = active_frames[idx]
            self._gif_label.place_configure(relx=0.5, rely=0.5, anchor="center")

    def _animate(self):
        if not self._overlay or not self._overlay.winfo_exists():
            self._anim_after = None
            return

        active_frames = self._scaled_frames or self._base_frames
        if active_frames:
            if self._current_frame >= len(active_frames):
                self._current_frame = 0
            self._gif_label.config(image=active_frames[self._current_frame], text="")
            self._gif_label.image = active_frames[self._current_frame]
            self._current_frame = (self._current_frame + 1) % len(active_frames)
            delay = 45
            if self._frame_delays and self._current_frame < len(self._frame_delays):
                delay = self._frame_delays[self._current_frame]
            self._anim_after = self._overlay.after(delay, self._animate)
            return

        # Fallback in-place gif decode (non-blocking, avoids static-first look when full frames not ready yet)
        if self._gif_path and os.path.exists(self._gif_path):
            try:
                inline_frame = tk.PhotoImage(file=self._gif_path, format=f"gif -index {self._current_frame}")
                self._gif_label.config(image=inline_frame, text="")
                self._gif_label.image = inline_frame
                self._current_frame += 1
                if self._current_frame > 100:
                    self._current_frame = 0
                self._anim_after = self._overlay.after(45, self._animate)
                return
            except Exception:
                pass

        # Fallback placeholder
        if self._first_frame is not None and self._gif_label and self._gif_label.winfo_exists():
            self._gif_label.config(image=self._first_frame, text="")
            self._gif_label.image = self._first_frame
            self._anim_after = self._overlay.after(100, self._animate)
            return

        self._anim_after = None

    def _finish_prepare_frames(self):
        if not self._overlay or not self._overlay.winfo_exists():
            return

        if not self._tk_frames and not self._pil_frames:
            self._gif_label.config(
                text="Brak assets/giphs/loading_app.gif",
                fg=self.theme.get("loading_muted", "#9aa3b2"),
                font=("Segoe UI", 10),
                image="",
            )
            self._gif_label.image = None
            return

        self._build_base_frames()
        self._build_scaled_frames()
        active_frames = self._scaled_frames or self._base_frames
        if active_frames:
            self._gif_label.config(image=active_frames[0], text="")
            self._gif_label.image = active_frames[0]
            self._current_frame = 0
            if self._anim_after is None:
                self._anim_after = self._overlay.after(45, self._animate)

    def _hex_to_rgb(self, value):
        value = str(value).lstrip("#")
        if len(value) != 6:
            return (15, 15, 20)
        return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))

    def _rgb_to_hex(self, rgb):
        r, g, b = rgb
        return f"#{max(0, min(255, int(r))):02x}{max(0, min(255, int(g))):02x}{max(0, min(255, int(b))):02x}"

    def _lerp_color(self, c1, c2, t):
        r1, g1, b1 = self._hex_to_rgb(c1)
        r2, g2, b2 = self._hex_to_rgb(c2)
        return self._rgb_to_hex((
            r1 + (r2 - r1) * t,
            g1 + (g2 - g1) * t,
            b1 + (b2 - b1) * t,
        ))

    def _destroy_overlay_now(self):
        if self._anim_after is not None and self._overlay and self._overlay.winfo_exists():
            try:
                self._overlay.after_cancel(self._anim_after)
            except Exception:
                pass
        self._anim_after = None

        if self._hide_anim_after is not None and self._overlay and self._overlay.winfo_exists():
            try:
                self._overlay.after_cancel(self._hide_anim_after)
            except Exception:
                pass
        self._hide_anim_after = None

        self._scaled_frames = []
        self._base_frames = []
        self._frame_delays = []
        self._last_size_key = None

        if self._overlay and self._overlay.winfo_exists():
            self._overlay.destroy()
        self._overlay = None
        self._gif_label = None
        self._hide_progress = 0.0

    def _hide_step(self):
        if not self._overlay or not self._overlay.winfo_exists():
            self._destroy_overlay_now()
            return

        self._hide_progress += 0.55
        t = min(1.0, self._hide_progress)

        bg_from = self._startup_bg
        bg_to = self.theme.get("bg_root", bg_from)
        bg_now = self._lerp_color(bg_from, bg_to, t)
        self._overlay.config(bg=bg_now)
        if self._gif_label and self._gif_label.winfo_exists():
            self._gif_label.config(bg=bg_now)

        if t < 1.0:
            self._hide_anim_after = self._overlay.after(12, self._hide_step)
        else:
            self._hide_anim_after = None
            self._destroy_overlay_now()

    def show(self, title_text=None, status_text=None, show_cancel=None):
        if self._overlay and self._overlay.winfo_exists():
            self._overlay.lift()
            return

        self._hide_requested = False
        self._shown_at = time.monotonic()

        self._overlay = tk.Frame(
            self.root,
            bg=self._startup_bg,
            highlightthickness=0,
            bd=0,
        )
        self._overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._overlay.lift()

        self._gif_label = tk.Label(
            self._overlay,
            bg=self._startup_bg,
            bd=0,
            highlightthickness=0,
            text="",
        )
        self._gif_label.place(relx=0.5, rely=0.5, anchor="center")
        self._overlay.bind("<Configure>", self._on_overlay_configure, add="+")

        self.root.update_idletasks()
        self._first_frame = self._load_first_frame_fast()
        initial_frame = self._first_frame
        if initial_frame is not None:
            self._gif_label.config(image=initial_frame, text="")
            self._gif_label.image = initial_frame
        else:
            self._gif_label.config(
                text="Wczytywanie...",
                fg=self.theme.get("loading_muted", "#9aa3b2"),
                font=("Segoe UI", 10),
            )

        self._overlay.after_idle(self._on_overlay_configure)
        self._start_prepare_frames()

        if self._anim_after is None:
            self._anim_after = self._overlay.after(45, self._animate)

    def _start_prepare_frames(self):
        self._tk_frames = []
        self._pil_frames = []
        self._frame_delays = []

        if Image is not None and ImageSequence is not None and ImageTk is not None:
            if self._load_thread and self._load_thread.is_alive():
                return
            self._load_thread = threading.Thread(target=self._load_frames_all_thread, daemon=True)
            self._load_thread.start()
        else:
            self._load_frames_all_fallback()

    def _load_frames_all_thread(self):
        if not os.path.exists(self._gif_path):
            self.root.after(0, self._finish_prepare_frames)
            return

        pil_frames = []
        frame_delays = []

        try:
            img = Image.open(self._gif_path)
            frame_iter = ImageSequence.Iterator(img) if ImageSequence is not None else [img]
            for frame in frame_iter:
                pil_frames.append(frame.copy().convert("RGBA"))
                dur = int(frame.info.get("duration", img.info.get("duration", 45)))
                frame_delays.append(max(16, min(200, dur)))
        except Exception:
            pil_frames = []
            frame_delays = []

        if pil_frames:
            self._pil_frames = pil_frames
            self._frame_delays = frame_delays
            self.root.after(0, self._finish_prepare_frames)
            return

        self.root.after(0, self._load_frames_all_fallback)

    def _load_frames_all_fallback(self):
        self._tk_frames = []
        self._frame_delays = []
        i = 0
        while True:
            try:
                frame = tk.PhotoImage(file=self._gif_path, format=f"gif -index {i}")
                self._tk_frames.append(frame)
                self._frame_delays.append(45)
                i += 1
            except Exception:
                break
        self._finish_prepare_frames()

    def hide(self):
        if not self._overlay or not self._overlay.winfo_exists():
            self._destroy_overlay_now()
            return
        if self._hide_anim_after is not None:
            return
        if self._hide_requested:
            return
        self._hide_requested = True

        frame_count = max(len(self._scaled_frames), len(self._tk_frames), len(self._pil_frames), 1)
        approx_one_loop_ms = frame_count * 45
        min_visible_ms = min(1400, max(650, approx_one_loop_ms))
        elapsed_ms = int((time.monotonic() - self._shown_at) * 1000)
        if elapsed_ms < min_visible_ms:
            delay = min_visible_ms - elapsed_ms
            self._hide_requested = False
            self._overlay.after(delay, self.hide)
            return

        self._hide_progress = 0.0
        self._hide_step()

    def set_loading_cancel_callback(self, callback):
        return

    def set_loading_cancel_enabled(self, enabled):
        return

    def set_loading_cancel_visible(self, visible):
        return

    def set_loading_progress(self, percent, status_text=None, smooth=True):
        return

    def set_loading_details(self, downloaded_bytes, total_bytes, speed_bytes_per_sec):
        return

    def set_loading_status(self, status_text):
        return

    def set_loading_indeterminate(self, enabled, status_text=None):
        return

    def apply_theme(self, theme):
        self.theme = theme
        if not self._overlay or not self._overlay.winfo_exists():
            return
        self._overlay.config(bg=self._startup_bg)
        if self._gif_label and self._gif_label.winfo_exists():
            self._gif_label.config(bg=self._startup_bg)


class StartupSplash:
    def __init__(self, root, theme):
        self.root = root
        self.window = None
        self.canvas = None
        self._image_id = None
        self._text_id = None
        self._frames = []
        self._delays = []
        self._frame_index = 0
        self._anim_after = None
        self._transparent_key = "#ff00ff"
        self._shell_color = "#11131a"
        self._window_size = (280, 340)

    def _resolve_gif_path(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        filename = "loading_app.gif"
        return os.path.join(base_dir, "assets", "giphs", filename)

    def _shell_bg(self):
        return self._shell_color

    def _shell_fg(self):
        return "#f2f5ff"

    def _load_frames(self):
        self._frames = []
        self._delays = []
        self._gif_path = self._resolve_gif_path()
        if not os.path.exists(self._gif_path):
            return

        if Image is not None and ImageSequence is not None and ImageTk is not None:
            try:
                img = Image.open(self._gif_path)
                for frame in ImageSequence.Iterator(img):
                    rgba = frame.copy().convert("RGBA")
                    scaled = self._scale_frame(rgba)
                    self._frames.append(ImageTk.PhotoImage(scaled))
                    dur = int(frame.info.get("duration", img.info.get("duration", 45)))
                    self._delays.append(max(16, min(200, dur)))
                return
            except Exception:
                self._frames = []
                self._delays = []

        i = 0
        while True:
            try:
                frame = tk.PhotoImage(file=self._gif_path, format=f"gif -index {i}")
                self._frames.append(frame)
                self._delays.append(45)
                i += 1
            except Exception:
                break

    def _scale_frame(self, frame):
        win_w, win_h = self._window_size
        max_w = int(win_w * 1.23)
        max_h = int(win_h * 1.23)
        src_w, src_h = frame.size
        scale = max(0.2, min(max_w / max(1, src_w), max_h / max(1, src_h)))
        out_w = max(1, int(round(src_w * scale)))
        out_h = max(1, int(round(src_h * scale)))
        resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.LANCZOS)
        return frame.resize((out_w, out_h), resample)

    def _center_geometry(self):
        width, height = self._window_size
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        return f"{width}x{height}+{x}+{y}"

    def _draw_shell(self):
        if not self.canvas or not self.canvas.winfo_exists():
            return
        self.canvas.delete("shell")
        width, height = self._window_size
        radius = 28
        fill = self._shell_bg()

        self.canvas.create_rectangle(radius, 0, width - radius, height, fill=fill, outline=fill, tags="shell")
        self.canvas.create_rectangle(0, radius, width, height - radius, fill=fill, outline=fill, tags="shell")
        self.canvas.create_oval(0, 0, radius * 2, radius * 2, fill=fill, outline=fill, tags="shell")
        self.canvas.create_oval(width - radius * 2, 0, width, radius * 2, fill=fill, outline=fill, tags="shell")
        self.canvas.create_oval(0, height - radius * 2, radius * 2, height, fill=fill, outline=fill, tags="shell")
        self.canvas.create_oval(width - radius * 2, height - radius * 2, width, height, fill=fill, outline=fill, tags="shell")

    def _content_center(self):
        width, height = self._window_size
        return width // 2, int((height // 2) * 0.87)

    def _animate(self):
        if not self.window or not self.window.winfo_exists() or not self.canvas or not self._frames or self._image_id is None:
            self._anim_after = None
            return
        self.canvas.itemconfigure(self._image_id, image=self._frames[self._frame_index])
        delay = self._delays[self._frame_index] if self._frame_index < len(self._delays) else 45
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self._anim_after = self.window.after(delay, self._animate)

    def show(self, title_text=None, status_text=None, show_cancel=None):
        if self.window and self.window.winfo_exists():
            try:
                self.window.lift()
            except Exception:
                pass
            return

        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(bg=self._transparent_key)
        try:
            self.window.wm_attributes("-transparentcolor", self._transparent_key)
        except Exception:
            pass

        self.canvas = tk.Canvas(
            self.window,
            width=self._window_size[0],
            height=self._window_size[1],
            bg=self._transparent_key,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self._draw_shell()
        center_x, center_y = self._content_center()
        self._image_id = self.canvas.create_image(center_x, center_y, anchor="center")

        self._load_frames()
        if self._frames:
            self.canvas.itemconfigure(self._image_id, image=self._frames[0])
            self._frame_index = 1 % len(self._frames)
            self._anim_after = self.window.after(45, self._animate)
        else:
            self._text_id = self.canvas.create_text(
                center_x,
                center_y,
                text="Wczytywanie...",
                fill=self._shell_fg(),
                font=("Segoe UI", 12, "bold"),
            )

        self.window.geometry(self._center_geometry())
        self.window.deiconify()
        self.window.lift()
        try:
            self.window.update_idletasks()
        except Exception:
            pass

    def hide(self):
        if not self.window or not self.window.winfo_exists():
            self.window = None
            self.canvas = None
            self._image_id = None
            self._text_id = None
            return
        if self._anim_after is not None:
            try:
                self.window.after_cancel(self._anim_after)
            except Exception:
                pass
            self._anim_after = None
        try:
            self.window.destroy()
        except Exception:
            pass
        self.window = None
        self.canvas = None
        self._image_id = None
        self._text_id = None

    def apply_theme(self, theme):
        return
