import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk
import sounddevice as sd

from gui.components.scrollbar_style import UltraThinScrollbar


class SettingsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.gui.root)
        self.withdraw()

        self.app = app
        self.app_state = app.state
        self.settings = app.settings

        self.bg_root = "#0e1016"
        self.bg_canvas = "#10131c"
        self.bg_card = "#171c28"
        self.bg_input = "#252c3d"
        self.fg_primary = "#f4f7ff"
        self.fg_muted = "#aeb7c9"
        self.accent = "#1fe38a"

        self.title("Ustawienia")
        self.geometry("440x560")
        self.minsize(400, 480)
        self.configure(bg=self.bg_root)
        self.resizable(False, False)

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.app.hotkeys.clear()

        self.create_layout()
        self.create_widgets()
        self.update_idletasks()
        self.deiconify()
        self.lift()


    def create_layout(self):
        self.container = tk.Frame(self, bg=self.bg_root)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.container,
            bg=self.bg_canvas,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.main_frame = tk.Frame(self.canvas, bg=self.bg_canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        self.scrollbar = UltraThinScrollbar(
            self.container,
            target_canvas=self.canvas,
            width=4,
            thumb_color="#3f4a67",
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
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        self.option_add("*TCombobox*Listbox.background", self.bg_input)
        self.option_add("*TCombobox*Listbox.foreground", self.fg_primary)
        self.option_add("*TCombobox*Listbox.selectBackground", "#34405a")
        self.option_add("*TCombobox*Listbox.selectForeground", self.fg_primary)
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

        style.configure(
            "Modern.TCombobox",
            fieldbackground=self.bg_input,
            background=self.bg_input,
            foreground=self.fg_primary,
            bordercolor=self.bg_input,
            lightcolor=self.bg_input,
            darkcolor=self.bg_input,
            arrowcolor=self.fg_primary,
            insertcolor=self.fg_primary,
            padding=6,
        )

        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", self.bg_input)],
            foreground=[("readonly", self.fg_primary)],
        )

    def _card(self, title):
        card = tk.Frame(self.main_frame, bg=self.bg_card)
        card.pack(fill="x", padx=16, pady=(0, 12))

        tk.Label(
            card,
            text=title,
            bg=self.bg_card,
            fg=self.fg_primary,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 8))

        return card

    def _row_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=self.bg_card,
            fg=self.fg_muted,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=14, pady=(4, 4))

    def create_widgets(self):
        self._configure_styles()

        tk.Label(
            self.main_frame,
            text="Ustawienia",
            bg=self.bg_canvas,
            fg=self.fg_primary,
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 4))

        tk.Label(
            self.main_frame,
            text="Urzadzenia audio, skroty i widok",
            bg=self.bg_canvas,
            fg=self.fg_muted,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18, pady=(0, 12))

        devices_card = self._card("Urzadzenia")

        self._row_label(devices_card, "Mikrofon")
        self.input_var = tk.StringVar()
        self.input_devices = [
            (i, d["name"])
            for i, d in enumerate(sd.query_devices())
            if d["max_input_channels"] > 0 and "WDM-KS" not in d["name"]
        ]
        input_names = [name for _, name in self.input_devices]

        self.input_combo = ttk.Combobox(
            devices_card,
            values=input_names,
            textvariable=self.input_var,
            state="readonly",
            style="Modern.TCombobox",
            cursor="hand2",
        )
        self.input_combo.pack(fill="x", padx=14, pady=(0, 8))
        self._bind_combobox_wheel_to_scroll(self.input_combo)

        self._row_label(devices_card, "Wyjscie (odsluch)")
        self.output_var = tk.StringVar()
        self.output_devices = [
            (i, d["name"])
            for i, d in enumerate(sd.query_devices())
            if d["max_output_channels"] > 0 and "WDM-KS" not in d["name"]
        ]
        output_names = [name for _, name in self.output_devices]

        self.output_combo = ttk.Combobox(
            devices_card,
            values=output_names,
            textvariable=self.output_var,
            state="readonly",
            style="Modern.TCombobox",
            cursor="hand2",
        )
        self.output_combo.pack(fill="x", padx=14, pady=(0, 14))
        self._bind_combobox_wheel_to_scroll(self.output_combo)

        self.set_current_devices()

        hotkeys_card = self._card("Skroty")

        self._row_label(hotkeys_card, "Efekty wl./wyl.")
        self.mic_hotkey_var = tk.StringVar(value=self.settings["hotkey_mic_mute"])
        self.mic_entry = self.create_hotkey_entry(hotkeys_card, self.mic_hotkey_var)
        self.mic_entry.pack(fill="x", padx=14, pady=(0, 8))

        self._row_label(hotkeys_card, "Odsluch wl./wyl.")
        self.monitor_hotkey_var = tk.StringVar(value=self.settings["hotkey_monitor_mute"])
        self.monitor_entry = self.create_hotkey_entry(hotkeys_card, self.monitor_hotkey_var)
        self.monitor_entry.pack(fill="x", padx=14, pady=(0, 8))

        self._row_label(hotkeys_card, "Calkowite wyciszenie")
        self.true_mic_mute_var = tk.StringVar(value=self.settings.get("hotkey_true_mic_mute", "F10"))
        self.true_mic_entry = self.create_hotkey_entry(hotkeys_card, self.true_mic_mute_var)
        self.true_mic_entry.pack(fill="x", padx=14, pady=(0, 14))

        view_card = self._card("Widok")
        self.meter_var = ctk.BooleanVar(value=self.app_state.show_meter)

        self.meter_checkbox = ctk.CTkCheckBox(
            view_card,
            text="Pokaz dolny meter",
            variable=self.meter_var,
            command=self.on_meter_toggle,
            fg_color=self.accent,
            hover_color="#1ac979",
            text_color=self.fg_primary,
            checkbox_height=18,
            checkbox_width=18,
            border_width=1,
            border_color="#38425a",
        )
        self.meter_checkbox.pack(anchor="w", padx=14, pady=(4, 14))

        actions = tk.Frame(self.main_frame, bg=self.bg_canvas)
        actions.pack(fill="x", padx=16, pady=(0, 16))
        actions.grid_columnconfigure(0, weight=1)
        actions.grid_columnconfigure(1, weight=1)

        tk.Button(
            actions,
            text="Anuluj",
            command=self.on_close,
            bg="#242a39",
            fg=self.fg_primary,
            activebackground="#2e364a",
            activeforeground=self.fg_primary,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=8,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        tk.Button(
            actions,
            text="Zapisz",
            command=self.save_and_close,
            bg=self.accent,
            fg="#04120a",
            activebackground="#2af099",
            activeforeground="#04120a",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=8,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))


    def set_current_devices(self):
        input_id = self.settings.get("default_input_device")
        output_id = self.settings.get("default_output_device")

        if input_id is not None:
            for idx, name in self.input_devices:
                if idx == input_id:
                    self.input_var.set(name)
                    break
        else:
            self.input_var.set("Domyslne systemowe")

        if output_id is not None:
            for idx, name in self.output_devices:
                if idx == output_id:
                    self.output_var.set(name)
                    break
        else:
            self.output_var.set("Domyslne systemowe")

    def _bind_combobox_wheel_to_scroll(self, combo):
        def on_wheel(event):
            self._on_mousewheel(event)
            return "break"

        combo.bind("<MouseWheel>", on_wheel)


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
                variable.set("Nacisnij klawisz...")
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


    def on_meter_toggle(self):
        pass


    def save_and_close(self):
        if not self.mic_hotkey_var.get() or not self.monitor_hotkey_var.get():
            messagebox.showerror("Blad", "Skroty nie moga byc puste")
            return

        mic = self.mic_hotkey_var.get().strip().lower()
        monitor = self.monitor_hotkey_var.get().strip().lower()
        true_mute = self.true_mic_mute_var.get().strip().lower()

        if len({mic, monitor, true_mute}) < 3:
            messagebox.showerror(
                "Blad",
                "Kazda akcja musi miec inny skrot.",
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

        self.app_state.default_input_device = input_id
        self.app_state.default_output_device = output_id

        self.settings["default_input_device"] = input_id
        self.settings["default_output_device"] = output_id
        self.settings["hotkey_mic_mute"] = self.mic_hotkey_var.get()
        self.settings["hotkey_monitor_mute"] = self.monitor_hotkey_var.get()
        self.settings["hotkey_true_mic_mute"] = self.true_mic_mute_var.get()
        self.settings["show_meter"] = self.meter_var.get()

        self.app_state.show_meter = self.meter_var.get()
        self.app.gui.update_meter_visibility()

        from core.settings import save_settings

        save_settings(self.settings)
        self.app.hotkeys.register()
        self.app.stream_manager.restart(input_id, output_id)
        self.destroy()


    def on_close(self):
        self.app.hotkeys.register()
        self.destroy()
