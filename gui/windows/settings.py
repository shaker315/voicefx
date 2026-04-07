import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import sounddevice as sd

from gui.components.scrollbar_style import UltraThinScrollbar
from gui.theme import get_theme


class SettingsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.gui.root)
        self.withdraw()

        self.app = app
        self.app_state = app.state
        self.settings = app.settings

        self.theme = get_theme(self.settings.get("theme", "dark"))
        self.bg_root = self.theme["bg_root"]
        self.bg_canvas = self.theme["bg_canvas"]
        self.bg_card = self.theme["bg_card"]
        self.bg_input = self.theme["bg_input"]
        self.fg_primary = self.theme["fg_primary"]
        self.fg_muted = self.theme["fg_muted"]
        self.accent = self.theme["accent"]
        self.card_border = self.theme["card_border"]
        self.button_bg = self.theme["button_bg"]
        self.button_bg_hover = self.theme["button_bg_hover"]

        self.title("Ustawienia")
        self.geometry("470x640")
        self.minsize(430, 540)
        self.configure(bg=self.bg_root)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app.hotkeys.clear()

        self.create_layout()
        self.create_widgets()
        self.update_idletasks()
        self.deiconify()
        self.lift()
        self.grab_set()

    def _is_virtual_output_device(self, device_name):
        name = str(device_name).lower()
        keywords = (
            "cable input",
            "vb-audio",
            "voicemeeter",
            "voice meeter",
            "virtual",
            "obs",
            "blackhole",
            "loopback",
        )
        return any(keyword in name for keyword in keywords)

    def create_layout(self):
        self.container = tk.Frame(self, bg=self.bg_root)
        self.container.pack(fill="both", expand=True)

        self.header = tk.Frame(self.container, bg=self.bg_root, height=96)
        self.header.pack(fill="x", padx=18, pady=(16, 10))
        self.header.pack_propagate(False)

        self.header_card = tk.Frame(
            self.header,
            bg=self.bg_card,
            highlightthickness=1,
            highlightbackground=self.card_border,
            bd=0,
        )
        self.header_card.pack(fill="both", expand=True)

        self.header_accent = tk.Frame(self.header_card, bg=self.accent, height=3)
        self.header_accent.pack(fill="x", side="top")

        self.header_body = tk.Frame(self.header_card, bg=self.bg_card)
        self.header_body.pack(fill="both", expand=True, padx=16, pady=14)

        self.canvas = tk.Canvas(
            self.container,
            bg=self.bg_canvas,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True, padx=(18, 0), pady=(0, 0))

        self.main_frame = tk.Frame(self.canvas, bg=self.bg_canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        self.scrollbar = UltraThinScrollbar(
            self.container,
            target_canvas=self.canvas,
            width=4,
            bg=self.theme["scrollbar_bg"],
            thumb_color=self.theme["scrollbar_thumb"],
            auto_hide_delay=1400,
        )

        self.main_frame.bind("<Configure>", self.update_scrollregion)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)
        self.main_frame.after_idle(self.update_scrollregion)

    def update_scrollregion(self, event=None):
        bbox = self.canvas.bbox("all")
        if not bbox:
            return

        self.canvas.configure(scrollregion=bbox)
        content_height = bbox[3] - bbox[1]
        canvas_height = self.canvas.winfo_height()

        if content_height > canvas_height:
            if not self.scrollbar.winfo_ismapped():
                self.scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor="ne", width=8)
        else:
            if self.scrollbar.winfo_ismapped():
                self.scrollbar.place_forget()
            self.canvas.yview_moveto(0)

    def _on_mousewheel(self, event):
        if not self.winfo_exists():
            return "break"
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return "break"
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _create_combo(self, parent, variable, values):
        combo = ctk.CTkComboBox(
            parent,
            variable=variable,
            values=values,
            state="readonly",
            font=("Segoe UI", 10),
            dropdown_font=("Segoe UI", 10),
            fg_color=self.bg_input,
            border_color=self.theme["checkbox_border"],
            button_color=self.bg_input,
            button_hover_color=self.theme["button_bg_hover"],
            text_color=self.fg_primary,
            dropdown_fg_color=self.bg_input,
            dropdown_text_color=self.fg_primary,
            dropdown_hover_color=self.theme["combo_select_bg"],
            corner_radius=8,
            height=34,
            width=100,
        )
        combo.configure(cursor="hand2")
        try:
            combo._entry.configure(cursor="hand2")
        except Exception:
            pass
        return combo

    def _card(self, title):
        shell = tk.Frame(self.main_frame, bg=self.bg_canvas)
        shell.pack(fill="x", padx=2, pady=(0, 14))

        card = tk.Frame(
            shell,
            bg=self.bg_card,
            highlightthickness=1,
            highlightbackground=self.card_border,
            bd=0,
        )
        card.pack(fill="x")

        top = tk.Frame(card, bg=self.bg_card, height=38)
        top.pack(fill="x")
        top.pack_propagate(False)

        accent_bar = tk.Frame(top, bg=self.accent, width=4)
        accent_bar.pack(side="left", fill="y")

        tk.Label(
            top,
            text=title.upper(),
            bg=self.bg_card,
            fg=self.fg_primary,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=(14, 14), pady=(9, 0))

        body = tk.Frame(card, bg=self.bg_card)
        body.pack(fill="x", padx=14, pady=(4, 14))

        return body

    def _row_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=self.bg_card,
            fg=self.fg_muted,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(6, 6))

    def create_widgets(self):
        tk.Label(
            self.header_body,
            text="Ustawienia",
            bg=self.bg_card,
            fg=self.fg_primary,
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")

        tk.Label(
            self.header_body,
            text="Audio, skróty i widok aplikacji",
            bg=self.bg_card,
            fg=self.fg_muted,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        devices_card = self._card("Urządzenia")

        self._row_label(devices_card, "Mikrofon")
        self.input_var = tk.StringVar()
        self.input_devices = [
            (i, d["name"])
            for i, d in enumerate(sd.query_devices())
            if d["max_input_channels"] > 0 and "WDM-KS" not in d["name"]
        ]
        input_names = ["Domyślne systemowe"] + [name for _, name in self.input_devices]

        self.input_combo = self._create_combo(devices_card, self.input_var, input_names)
        self.input_combo.pack(fill="x", pady=(0, 8))
        self._bind_combobox_wheel_to_scroll(self.input_combo)

        self._row_label(devices_card, "Wyjście (odsłuch)")
        self.output_var = tk.StringVar()
        self.output_devices = [
            (i, d["name"])
            for i, d in enumerate(sd.query_devices())
            if d["max_output_channels"] > 0 and "WDM-KS" not in d["name"]
        ]
        output_names = ["Domyślne systemowe"] + [name for _, name in self.output_devices]

        self.output_combo = self._create_combo(devices_card, self.output_var, output_names)
        self.output_combo.pack(fill="x", pady=(0, 14))
        self._bind_combobox_wheel_to_scroll(self.output_combo)

        self._row_label(devices_card, "Wyjście aplikacji (np. OBS, VB-Cable)")
        self.virtual_output_var = tk.StringVar()
        self.virtual_output_devices = [
            (i, d["name"])
            for i, d in enumerate(sd.query_devices())
            if d["max_output_channels"] > 0
            and "WDM-KS" not in d["name"]
            and self._is_virtual_output_device(d["name"])
        ]
        virtual_output_names = ["Auto"] + [name for _, name in self.virtual_output_devices]

        self.virtual_output_combo = self._create_combo(devices_card, self.virtual_output_var, virtual_output_names)
        self.virtual_output_combo.pack(fill="x", pady=(0, 14))
        self._bind_combobox_wheel_to_scroll(self.virtual_output_combo)

        self.set_current_devices()

        hotkeys_card = self._card("Skróty")

        self._row_label(hotkeys_card, "Efekty wł./wył.")
        self.mic_hotkey_var = tk.StringVar(value=self.settings["hotkey_mic_mute"])
        self.mic_entry = self.create_hotkey_entry(hotkeys_card, self.mic_hotkey_var)
        self.mic_entry.pack(fill="x", pady=(0, 8))

        self._row_label(hotkeys_card, "Odsłuch wł./wył.")
        self.monitor_hotkey_var = tk.StringVar(value=self.settings["hotkey_monitor_mute"])
        self.monitor_entry = self.create_hotkey_entry(hotkeys_card, self.monitor_hotkey_var)
        self.monitor_entry.pack(fill="x", pady=(0, 8))

        self._row_label(hotkeys_card, "Całkowite wyciszenie")
        self.true_mic_mute_var = tk.StringVar(value=self.settings.get("hotkey_true_mic_mute", "F10"))
        self.true_mic_entry = self.create_hotkey_entry(hotkeys_card, self.true_mic_mute_var)
        self.true_mic_entry.pack(fill="x", pady=(0, 14))

        view_card = self._card("Widok")
        self.meter_var = ctk.BooleanVar(value=self.app_state.show_meter)

        self.meter_checkbox = ctk.CTkCheckBox(
            view_card,
            text="Pokaż meter",
            variable=self.meter_var,
            fg_color=self.accent,
            hover_color=self.theme["accent_hover"],
            text_color=self.fg_primary,
            checkbox_height=18,
            checkbox_width=18,
            border_width=1,
            border_color=self.theme["checkbox_border"],
        )
        self.meter_checkbox.pack(anchor="w", pady=(4, 14))

        self._row_label(view_card, "Wygląd")
        self.theme_var = tk.StringVar(
            value="Jasny" if self.settings.get("theme") == "light" else "Ciemny"
        )
        self.theme_combo = self._create_combo(view_card, self.theme_var, ["Ciemny", "Jasny"])
        self.theme_combo.pack(fill="x", pady=(0, 14))
        self._bind_combobox_wheel_to_scroll(self.theme_combo)

        actions = tk.Frame(self.main_frame, bg=self.bg_canvas)
        actions.pack(fill="x", padx=2, pady=(0, 18))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        self.cancel_btn = ctk.CTkButton(
            actions,
            text="Anuluj",
            command=self.on_close,
            fg_color=self.button_bg,
            hover_color=self.button_bg_hover,
            text_color=self.theme["button_text"],
            border_width=1,
            border_color=self.card_border,
            corner_radius=10,
            height=40,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
        )
        self.cancel_btn.grid(row=0, column=0, sticky="ew", padx=(0, 7))

        self.save_btn = ctk.CTkButton(
            actions,
            text="Zapisz",
            command=self.save_and_close,
            fg_color=self.accent,
            hover_color=self.theme["accent_hover"],
            text_color=self.theme["button_text_dark"],
            corner_radius=10,
            height=40,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
        )
        self.save_btn.grid(row=0, column=1, sticky="ew", padx=(7, 0))


    def set_current_devices(self):
        input_id = self.settings.get("default_input_device")
        output_id = self.settings.get("default_output_device")
        virtual_output_id = self.settings.get("default_virtual_output_device")

        if input_id is not None:
            for idx, name in self.input_devices:
                if idx == input_id:
                    self.input_var.set(name)
                    break
        else:
            self.input_var.set("Domyślne systemowe")

        if output_id is not None:
            for idx, name in self.output_devices:
                if idx == output_id:
                    self.output_var.set(name)
                    break
        else:
            self.output_var.set("Domyślne systemowe")

        if virtual_output_id is not None:
            if virtual_output_id == -1:
                self.virtual_output_var.set("Brak")
                return
            for idx, name in self.virtual_output_devices:
                if idx == virtual_output_id:
                    self.virtual_output_var.set(name)
                    break
            else:
                self.virtual_output_var.set("Auto")
        else:
            self.virtual_output_var.set("Auto")

    def _bind_combobox_wheel_to_scroll(self, combo):
        def on_wheel(event):
            self._on_mousewheel(event)
            return "break"

        combo.bind("<MouseWheel>", on_wheel)
        try:
            combo._entry.bind("<MouseWheel>", on_wheel)
        except Exception:
            pass


    def create_hotkey_entry(self, parent, variable):
        entry = tk.Entry(
            parent,
            textvariable=variable,
            font=("Segoe UI", 11),
            bg=self.bg_input,
            fg=self.fg_primary,
            justify="center",
            state="readonly",
            readonlybackground=self.bg_input,
            relief="flat",
            insertbackground=self.fg_primary,
            cursor="hand2",
        )

        listening = {"active": False}

        def start_listen(event=None):
            if not listening["active"]:
                listening["active"] = True
                variable.set("Naciśnij klawisz...")
                entry.config(fg="#ff6b6b", state="normal")
                entry.delete(0, tk.END)

        def stop_listen():
            if listening["active"]:
                listening["active"] = False
                entry.config(fg=self.fg_primary, state="readonly")

        def on_key_press(event):
            if listening["active"]:
                mods = []
                state = event.state

                if state & 0x0001:
                    mods.append("shift")
                if state & 0x0004:
                    mods.append("ctrl")
                if state & 0x0008:
                    mods.append("alt")

                key = event.keysym.lower()
                if key in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"):
                    return "break"

                combo = "+".join(mods + [key])
                variable.set(combo)
                stop_listen()
                return "break"

        entry.bind("<Button-1>", start_listen)
        entry.bind("<Key>", on_key_press)
        entry.bind("<FocusOut>", lambda e: stop_listen())

        entry.bind("<KeyRelease>", lambda e: "break")
        entry.bind("<Control-v>", lambda e: "break")
        entry.bind("<Control-c>", lambda e: "break")
        entry.bind("<Button-3>", lambda e: "break")

        return entry


    def save_and_close(self):
        if not self.mic_hotkey_var.get() or not self.monitor_hotkey_var.get():
            messagebox.showerror("Błąd", "Skróty nie mogą być puste")
            return

        mic = self.mic_hotkey_var.get().strip().lower()
        monitor = self.monitor_hotkey_var.get().strip().lower()
        true_mute = self.true_mic_mute_var.get().strip().lower()

        if len({mic, monitor, true_mute}) < 3:
            messagebox.showerror(
                "Błąd",
                "Każda akcja musi mieć inny skrót.",
            )
            return

        input_id = None
        selected_input = self.input_var.get()
        for idx, name in self.input_devices:
            if name == selected_input:
                input_id = idx

        output_id = None
        selected_output = self.output_var.get()
        for idx, name in self.output_devices:
            if name == selected_output:
                output_id = idx

        virtual_output_id = None
        selected_virtual_output = self.virtual_output_var.get()
        if selected_virtual_output != "Auto":
            for idx, name in self.virtual_output_devices:
                if name == selected_virtual_output:
                    virtual_output_id = idx

        self.app_state.default_input_device = input_id
        self.app_state.default_output_device = output_id
        self.app_state.default_virtual_output_device = virtual_output_id

        self.settings["default_input_device"] = input_id
        self.settings["default_output_device"] = output_id
        self.settings["default_virtual_output_device"] = virtual_output_id
        self.settings["hotkey_mic_mute"] = self.mic_hotkey_var.get()
        self.settings["hotkey_monitor_mute"] = self.monitor_hotkey_var.get()
        self.settings["hotkey_true_mic_mute"] = self.true_mic_mute_var.get()
        self.settings["show_meter"] = self.meter_var.get()
        selected_theme = "light" if self.theme_var.get() == "Jasny" else "dark"
        self.settings["theme"] = selected_theme

        self.app_state.show_meter = self.meter_var.get()
        self.app_state.theme = selected_theme

        from core.settings import save_settings

        save_settings(self.settings)
        self.app.hotkeys.register()
        self.app.stream_manager.restart(input_id, output_id, virtual_output_id)
        gui = getattr(self.app, "gui", None)
        if gui and hasattr(gui, "root") and gui.root.winfo_exists():
            gui.root.after(
                10,
                lambda: (
                    gui.update_meter_visibility(),
                    gui.apply_theme(selected_theme),
                    gui.refresh_scroll_bindings(),
                ),
            )
        self.destroy()


    def on_close(self):
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass
        self.app.hotkeys.register()
        gui = getattr(self.app, "gui", None)
        if gui and hasattr(gui, "refresh_scroll_bindings"):
            gui.refresh_scroll_bindings()
        self.destroy()
