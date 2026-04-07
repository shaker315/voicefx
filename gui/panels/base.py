import math
import tkinter as tk
import tkinter.font as tkfont


class PanelBase:
    def __init__(self, ui):
        self.ui = ui

    @property
    def theme(self):
        return self.ui.theme

    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill, outline="", tag=None, width=1):
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
        return canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=36,
            fill=fill,
            outline=outline,
            width=width,
            tags=tag,
        )

    def draw_badge_capsule(self, canvas, x1, y1, x2, y2, fill, outline, tag=None, width=1):
        h = max(1.0, float(y2 - y1))
        r = h / 2.0
        left = x1 + r
        right = x2 - r

        if right > left:
            canvas.create_rectangle(left, y1, right, y2, fill=fill, outline="", tags=tag)
        canvas.create_oval(x1, y1, x1 + 2 * r, y2, fill=fill, outline="", tags=tag)
        canvas.create_oval(x2 - 2 * r, y1, x2, y2, fill=fill, outline="", tags=tag)

        if not outline:
            return

        if right > left:
            canvas.create_line(left, y1, right, y1, fill=outline, width=width, tags=tag)
            canvas.create_line(left, y2, right, y2, fill=outline, width=width, tags=tag)
        canvas.create_arc(
            x1, y1, x1 + 2 * r, y2,
            start=90, extent=180,
            style="arc",
            outline=outline,
            width=width,
            tags=tag,
        )
        canvas.create_arc(
            x2 - 2 * r, y1, x2, y2,
            start=270, extent=180,
            style="arc",
            outline=outline,
            width=width,
            tags=tag,
        )

    def create_rounded_section(
        self,
        parent,
        row,
        pady,
        sticky="ew",
        min_height=140,
        auto_fit=False,
        badge_height=34,
    ):
        badge_overlap = max(0, int(badge_height / 2))
        panel = tk.Canvas(
            parent,
            bg=self.theme["bg_root"],
            highlightthickness=0,
            bd=0,
            height=min_height + badge_overlap,
        )
        panel.grid(row=row, column=0, sticky=sticky, padx=10, pady=pady)
        panel.grid_columnconfigure(0, weight=1)
        panel._badge_overlap = badge_overlap
        panel._badge_height = badge_height
        panel._content_min_height = min_height

        inner = tk.Frame(panel, bg=self.theme["bg_card"])
        window_id = panel.create_window((18, 18 + badge_overlap), window=inner, anchor="nw")

        def redraw(event=None):
            raw_width = panel.winfo_width() - 2
            raw_height = panel.winfo_height() - 2
            width = max(raw_width, 40)
            height = max(raw_height, 40)
            panel.delete("rounded_bg")
            self.draw_rounded_rect(
                panel,
                1,
                1 + badge_overlap,
                width,
                height,
                radius=24,
                fill=self.theme["bg_card"],
                outline=self.theme["card_border"],
                tag="rounded_bg",
                width=2,
            )
            panel.tag_lower("rounded_bg")
            panel.coords(window_id, 18, 18 + badge_overlap)
            panel.itemconfig(window_id, width=max(0, width - 36))
            if not auto_fit:
                panel.itemconfig(window_id, height=max(0, height - badge_overlap - 36))
            if hasattr(panel, "_redraw_badge"):
                panel._redraw_badge()

        def fit_height(event=None):
            if auto_fit:
                panel.configure(height=max(min_height + badge_overlap, inner.winfo_reqheight() + badge_overlap + 36))

        panel._redraw_card = redraw
        panel.bind("<Configure>", redraw)
        if auto_fit:
            inner.bind("<Configure>", fit_height)
        redraw()
        return panel, inner

    def draw_badge_reset_icon(self, canvas, center_x, center_y, color, tags=None):
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
            tags=tags,
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

        canvas.create_line(tip_x, tip_y, lx, ly, fill=color, width=1.8, tags=tags)
        canvas.create_line(tip_x, tip_y, rx, ry, fill=color, width=1.8, tags=tags)

    def create_section_badge(
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
        badge = parent
        badge.display_text = text
        badge._badge_width = width
        badge._badge_height = height
        badge._text_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        badge._popup_action = popup_action
        badge._popup_tooltip_text = popup_tooltip_text or "Personalizacja"
        badge.config(cursor="arrow")

        def redraw(event=None):
            try:
                if not badge.winfo_exists():
                    return
                badge.delete("badge")
                current_width = max(40, badge._badge_width)
                current_height = max(24, badge._badge_height)
                center_x = badge.winfo_width() / 2
                center_y = max(1, getattr(badge, "_badge_overlap", int(current_height / 2)))
                x1 = center_x - (current_width / 2)
                y1 = center_y - (current_height / 2)
                x2 = center_x + (current_width / 2)
                y2 = center_y + (current_height / 2)
                badge.badge_bounds = (x1, y1, x2, y2)
                self.draw_badge_capsule(
                    badge,
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=self.theme["bg_card"],
                    outline=self.theme["card_border"],
                    tag="badge",
                    width=2,
                )
                label = badge.display_text
                popup_shift = 9 if badge._popup_action else 0
                text_x = center_x - popup_shift
                badge.create_text(
                    text_x,
                    center_y,
                    text=label,
                    fill=self.theme["fg_primary"],
                    font=badge._text_font,
                    tags="badge",
                )

                if badge._popup_action:
                    text_width = badge._text_font.measure(label)
                    popup_x = text_x + (text_width / 2) + 11
                    popup_y = center_y + 1
                    badge.create_text(
                        popup_x,
                        popup_y,
                        text="\u25be",
                        fill=self.theme["fg_primary"],
                        font=("Segoe UI", 9, "bold"),
                        tags="badge",
                    )
                    badge.popup_center = (popup_x, popup_y)
                else:
                    badge.popup_center = None
                if action:
                    icon_x = x2 - 16
                    icon_y = center_y
                    self.draw_badge_reset_icon(
                        badge,
                        icon_x,
                        icon_y,
                        getattr(badge, "_reset_color", self.theme["slider_reset"]),
                        tags="badge",
                    )
                    badge.action_center = (icon_x, icon_y)
                else:
                    badge.action_center = None
            except tk.TclError:
                return

        badge._reset_angle = 0
        badge._reset_color = self.theme["slider_reset"]
        badge._reset_spin_after_id = None
        badge._reset_settle_after_id = None
        badge._reset_flash_after_id = None
        badge._redraw_badge = redraw
        badge._action = action
        badge._tooltip_text = tooltip_text or text
        badge._tooltip_window = None

        def show_badge_tooltip(event, label):
            if badge._tooltip_window or not label:
                return
            tw = tk.Toplevel(badge)
            tw.wm_overrideredirect(True)
            item = tk.Label(
                tw,
                text=label,
                background="#333333",
                foreground="white",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 10),
            )
            item.pack()
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

        badge.bind("<Button-1>", on_badge_click, add="+")
        badge.bind("<Motion>", on_badge_motion, add="+")
        badge.bind("<Leave>", lambda event: (badge.config(cursor="arrow"), hide_badge_tooltip()), add="+")
        redraw()
        return badge

    def set_badge_text(self, badge, text):
        if not badge or not badge.winfo_exists():
            return
        badge.display_text = text
        if hasattr(badge, "_redraw_badge"):
            badge._redraw_badge()

    def get_badge_screen_bounds(self, badge):
        if not badge or not badge.winfo_exists():
            return None
        x1, y1, x2, y2 = getattr(
            badge,
            "badge_bounds",
            (0, 0, badge.winfo_width(), badge.winfo_height()),
        )
        root_x = badge.winfo_rootx()
        root_y = badge.winfo_rooty()
        return (root_x + x1, root_y + y1, root_x + x2, root_y + y2)
