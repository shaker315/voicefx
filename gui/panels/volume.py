import tkinter as tk

from gui.components.meter import MasterMeter
from gui.components.scrollbar_style import UltraThinScrollbar
from gui.components.slider import ModernSlider
from gui.components.tooltip import Tooltip
from .base import PanelBase


class VolumePanel(PanelBase):
    def build(self):
        ui = self.ui

        ui.primary_section, ui.primary_inner = self.create_rounded_section(
            ui.main_frame, row=1, pady=(2, 0), min_height=210, auto_fit=False
        )
        ui.primary_badge = self.create_section_badge(ui.primary_section, "Głośność")
        ui.primary_inner.grid_columnconfigure(0, weight=1)
        ui.primary_inner.grid_rowconfigure(0, weight=1)

        ui.primary_scroll_host = tk.Frame(ui.primary_inner, bg=ui.theme["bg_card"])
        ui.primary_scroll_host.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=(4, 4))
        ui.primary_scroll_host.grid_columnconfigure(0, weight=1)
        ui.primary_scroll_host.grid_rowconfigure(0, weight=1)
        ui.primary_scroll_host.grid_propagate(False)

        ui.primary_canvas = tk.Canvas(
            ui.primary_scroll_host,
            bg=ui.theme["bg_card"],
            highlightthickness=0,
            bd=0,
        )
        ui.primary_canvas.grid(row=0, column=0, sticky="nsew")

        ui.primary_scrollbar = UltraThinScrollbar(
            ui.primary_scroll_host,
            target_canvas=ui.primary_canvas,
            width=3,
            bg=ui.theme["bg_card"],
            thumb_color=ui.theme["scrollbar_thumb"],
            auto_hide_delay=1500,
        )

        ui.primary_list = tk.Frame(ui.primary_canvas, bg=ui.theme["bg_card"])
        ui.primary_window_id = ui.primary_canvas.create_window((0, 0), window=ui.primary_list, anchor="nw")
        ui.primary_list.grid_columnconfigure(0, weight=1)
        ui.primary_list.bind("<Configure>", ui.update_primary_scrollregion)
        ui.primary_canvas.bind("<Configure>", ui.on_primary_canvas_configure)

        slider = ModernSlider(
            ui.primary_list,
            "Głośność mikrofonu",
            ui.app_state,
            "volume",
            0.2,
            10.0,
            save_callback=ui.save_settings,
            default_value=1,
            theme=ui.theme,
        )
        slider.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 2))
        ui.sliders.append(slider)

        slider = ModernSlider(
            ui.primary_list,
            "Odsłuch",
            ui.app_state,
            "monitor_volume",
            0.05,
            2.0,
            save_callback=ui.save_settings,
            default_value=1,
            theme=ui.theme,
        )
        slider.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))
        ui.sliders.append(slider)

    def create_meter(self):
        ui = self.ui
        if ui.settings.get("show_meter", True):
            self._create_meter_section()
            ui._bind_scroll_targets()
        else:
            ui.meter_frame = None
            ui.meter_header = None
            ui.meter_label = None
            ui.meter_toggle = None
            ui.meter = None

    def update_meter_visibility(self):
        ui = self.ui
        if not ui.root.winfo_exists():
            return
        if ui.app_state.show_meter:
            if not hasattr(ui, "meter") or ui.meter is None:
                self._create_meter_section()
                ui._bind_scroll_targets()
        else:
            if hasattr(ui, "meter_frame") and ui.meter_frame:
                ui.meter_frame.destroy()
                ui.meter_frame = None
                ui.meter_header = None
                ui.meter_label = None
                ui.meter_toggle = None
            ui.meter = None
        ui._bind_scroll_targets()
        ui.update_sections_layout()

    def _create_meter_section(self):
        ui = self.ui
        ui.meter_frame = tk.Frame(ui.primary_list, bg=ui.theme["bg_card"])
        ui.meter_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 8))
        ui.meter_frame.grid_columnconfigure(0, weight=1)

        ui.meter_header = tk.Frame(ui.meter_frame, bg=ui.theme["bg_card"])
        ui.meter_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 1))
        ui.meter_header.grid_columnconfigure(0, weight=1)

        ui.meter_label = tk.Label(
            ui.meter_header,
            text="Meter",
            bg=ui.theme["bg_card"],
            fg=ui.theme["slider_text"],
            font=("Segoe UI", 10, "bold"),
        )
        ui.meter_label.grid(row=0, column=0, sticky="w")

        ui.meter_toggle = tk.Canvas(
            ui.meter_header,
            width=12,
            height=12,
            bg=ui.theme["bg_card"],
            highlightthickness=0,
            cursor="hand2",
        )
        ui.meter_toggle.grid(row=0, column=1, sticky="e", padx=(8, 0))
        ui.meter_toggle.bind("<Button-1>", self._toggle_meter_gate)
        Tooltip(ui.meter_toggle, "Bramka szumow")
        self.draw_meter_toggle()

        ui.meter = MasterMeter(
            ui.meter_frame,
            ui.app_state,
            theme=ui.theme,
            save_callback=ui.save_settings,
            show_gate_toggle=False,
        )
        ui.meter.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 2))

    def draw_meter_toggle(self):
        ui = self.ui
        if not hasattr(ui, "meter_toggle") or not ui.meter_toggle or not ui.meter_toggle.winfo_exists():
            return
        ui.meter_toggle.delete("all")
        color = ui.theme["accent"] if ui.app_state.noise_gate_on else ui.theme["danger"]
        ui.meter_toggle.create_oval(2, 2, 10, 10, fill=color, outline="")

    def _toggle_meter_gate(self, event=None):
        ui = self.ui
        ui.app_state.noise_gate_on = not ui.app_state.noise_gate_on
        self.draw_meter_toggle()
        if ui.meter and ui.meter.winfo_exists():
            ui.meter.draw()
        ui.save_settings()

    def get_primary_core_content_height(self):
        ui = self.ui
        if not hasattr(ui, "primary_list") or not ui.primary_list.winfo_exists():
            return 130

        ui.primary_list.update_idletasks()
        row_heights = {}
        for widget in ui.primary_list.grid_slaves():
            info = widget.grid_info()
            row = int(info.get("row", 0))
            row_heights[row] = max(row_heights.get(row, 0), widget.winfo_reqheight())

        if not row_heights:
            return 130

        return sum(row_heights.values()) + 48
