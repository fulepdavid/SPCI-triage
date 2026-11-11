import queue
import random
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

from config import SHOW_IMAGE_OVERLAY, SIMULATE_DEVICES, resource_path
from theme import COLORS, FONTS
from widgets import VirtualKeyboard

def bp_answer(r):
        """Bilingual answer for the PDF. 'data' keeps the raw values for later sending."""
        spo2 = "–" if r["spo2"] is None else f"{r['spo2']} %"
        spo2_pulse_hu = "–" if r["spo2_pulse"] is None else f"{r['spo2_pulse']}/perc"
        spo2_pulse_en = "–" if r["spo2_pulse"] is None else f"{r['spo2_pulse']} bpm"
        return {
            "hu": (f"Vérnyomás: {r['nibp_sys']}/{r['nibp_dia']} mmHg\n"
                f"Átlagnyomás (MAP): {r['nibp_mean']} mmHg\n"
                f"Pulzus (vérnyomásmérő): {r['nibp_pulse']}/perc\n"
                f"SpO2: {spo2} · Pulzus (SpO2): {spo2_pulse_hu}"),
            "en": (f"Blood pressure: {r['nibp_sys']}/{r['nibp_dia']} mmHg\n"
                f"Mean arterial pressure (MAP): {r['nibp_mean']} mmHg\n"
                f"Pulse (BP monitor): {r['nibp_pulse']} bpm\n"
                f"SpO2: {spo2} · Pulse (SpO2): {spo2_pulse_en}"),
            "data": {
                "nibp_sys": r["nibp_sys"],
                "nibp_dia": r["nibp_dia"],
                "nibp_mean": r["nibp_mean"],
                "nibp_pulse": r["nibp_pulse"],
                "spo2": r["spo2"],
                "spo2_pulse": r["spo2_pulse"],
                "measured_at": r["measured_at"],
            },
        }
        
class QuestionMixin:
    """Renders one question at a time and stores the answers."""

    def _new_btn_frame(self):
        frame = ctk.CTkFrame(self.q_frame, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=42, pady=35)
        return frame

    def show_question(self):
        self.btn_frame.destroy()
        self.btn_frame = self._new_btn_frame()

        questions = self.q_data["questions"]
        if self.session["index"] >= len(questions):
            self.finish_questionnaire()
            return

        q = questions[self.session["index"]]
        self.selected_option = None
        self.question_label.configure(text=self.tr(q["text"]))
        self.update_footer()

        if q["type"] == "choice":
            self.show_choice_question(q)
        elif q["type"] == "bodymap":
            self.show_image_question(q)
        elif q["type"] == "measurement":
            self.show_measurement_question(q)
        elif q["type"] == "text":
            self.show_text_question(q)
        elif q["type"] == "button":
            self.subtitle_label.grid_remove()
            self.show_button_question(q)

    def answer(self, value):
        q = self.q_data["questions"][self.session["index"]]
        label = q.get("answer_label", q["text"])
        self.session["answers"].append({"question": label, "answer": value})
        self.session["index"] += 1
        self.show_question()

    def show_choice_question(self, q):
        cols = q.get("layout", {}).get("cols", 1)
        options = q["options"]

        self.choice_var = tk.StringVar(value="")
        self.choice_widgets = []

        rows = (len(options) + cols - 1) // cols
        for r in range(rows):
            self.btn_frame.grid_rowconfigure(r, weight=1)
        for c in range(cols):
            self.btn_frame.grid_columnconfigure(c, weight=1)

        for i, opt in enumerate(options):
            card = ctk.CTkFrame(self.btn_frame, fg_color=COLORS["white"], border_width=1.5,
                                border_color=COLORS["border"], corner_radius=14, height=98)
            card.grid(row=i // cols, column=i % cols, sticky="nsew", padx=8, pady=8)
            card.grid_propagate(False)

            radio = ctk.CTkRadioButton(
                card,
                text=self.tr(opt),
                variable=self.choice_var,
                value=str(i),
                font=FONTS["body"],
                text_color=COLORS["text"],
                fg_color=COLORS["primary"],
                hover_color=COLORS["primary_hover"],
                border_color=COLORS["muted"],
                border_width_unchecked=3,
                border_width_checked=6,
                radiobutton_width=35,
                radiobutton_height=35,
                command=lambda o=opt, idx=i: self.select_option(o, idx),
            )
            radio.pack(fill="both", expand=True, padx=20)
            card.bind("<Button-1>", lambda e, r=radio: r.invoke())
            self.choice_widgets.append(card)

    def select_option(self, option, index):
        self.selected_option = option
        for i, card in enumerate(self.choice_widgets):
            if i == index:
                card.configure(border_color=COLORS["primary"], fg_color=COLORS["primary_light"])
            else:
                card.configure(border_color=COLORS["border"], fg_color=COLORS["white"])
        self.next_button.configure(state="normal")

    def show_image_question(self, q):
        self.canvas = tk.Canvas(self.btn_frame, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.images = []

        for img_data in q["images"]:
            image = tk.PhotoImage(file=resource_path(img_data["image"]))
            self.images.append(image)  # keep a reference, or Tk drops the image
            x, y = img_data["image_position"]

            image_id = self.canvas.create_image(x, y, anchor="nw", image=image)

            if SHOW_IMAGE_OVERLAY:
                for region in img_data["regions"]:
                    x1, y1, x2, y2 = region["rect"]
                    rect = self.canvas.create_rectangle(x + x1, y + y1, x + x2, y + y2,
                                                        outline="red", width=2)
                    text = self.canvas.create_text(x + (x1 + x2) / 2, y + (y1 + y2) / 2,
                                                   text=region["name"])
                    for item in (rect, text):
                        self.canvas.tag_bind(item, "<Button-1>",
                                             lambda e, data=img_data: self.image_click(e, data))

            self.canvas.tag_bind(image_id, "<Button-1>",
                                 lambda e, data=img_data: self.image_click(e, data))

    def image_click(self, event, image_data):
        img_x, img_y = image_data["image_position"]
        x = event.x - img_x
        y = event.y - img_y
        for region in image_data["regions"]:
            x1, y1, x2, y2 = region["rect"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.answer(region["name"])
                return

    def show_text_question(self, q):
        self.error_label = tk.Label(self.btn_frame, text="", font=("Arial", 20), fg="red")
        self.error_label.pack(pady=10)

        keyboard = VirtualKeyboard(self.btn_frame, language=self.language,
                                   keyboard_type=q["keyboard_type"])

        entry = tk.Entry(self.btn_frame, font=("Arial", 24))

        def entry_focused(event):
            keyboard.entry = event.widget
            keyboard.input_buffer = ""
            if not keyboard.winfo_ismapped():
                keyboard.pack(side="bottom", fill="x")

        entry.bind("<FocusIn>", entry_focused)
        entry.bind("<Key>", lambda e: "break")   # input only through the virtual keyboard
        entry.pack(fill="x", padx=50, pady=30)
        entry.focus_set()

        def submit():
            value = keyboard.get_value().strip()

            if q.get("required", False) and not value:
                self.error_label.configure(text=self.tr(q["error_label"]))
                return

            if q.get("id") == "TAJSZAM" and len(value) != 9:
                self.error_label.configure(text=self.tr(q["error_label"]))
                return

            if q.get("keyboard_type") == "date":
                try:
                    datetime.strptime(value, "%Y%m%d")
                except ValueError:
                    self.error_label.configure(text="Please enter a valid date.")
                    return

            self.error_label.configure(text="")
            self.answer(value)

        tk.Button(self.btn_frame, text="Tovább" if self.language == "hu" else "Next",
                  font=("Arial", 24, "bold"), command=submit).pack(pady=20)

    def show_measurement_question(self, q):
        if SIMULATE_DEVICES:
            self.status = tk.Label(self.btn_frame, text="Mérés folyamatban...", font=("Arial", 20))
            self.status.pack(pady=20)
            tk.Button(self.btn_frame, text="Szimulált mérés", font=("Arial", 22),
                      command=lambda: self.measure_device(q["device"])).pack(pady=20)
            return

        if q["device"] != "bp":
            self.show_device_unavailable()
            return

        self.status = tk.Label(self.btn_frame, text="Mérés folyamatban...", font=("Arial", 20))
        self.status.pack(pady=20)

        self.measuring = True
        if self.timeout_job is not None:
            self.after_cancel(self.timeout_job)
            self.timeout_job = None

        self.measure_queue = queue.Queue()
        self.bp.start(self.measure_queue)
        self.poll_job = self.after(200, self.poll_measurement)

    def measure_device(self, device):
        """Development only: simulated values, used when SIMULATE_DEVICES is True."""
        if device == "thermometer":
            value = round(random.uniform(36.2, 39.5), 1)
        elif device == "pulse":
            value = random.randint(55, 120)
        else:
            value = None
        self.answer(value)

    def show_device_unavailable(self):
        self.status = tk.Label(
            self.btn_frame,
            text=self.tr({
                "hu": "Az eszköz nem elérhető. Kérjük, szóljon a személyzetnek.",
                "en": "The device is unavailable. Please inform the staff.",
            }),
            font=("Arial", 20),
            wraplength=900,
        )
        self.status.pack(pady=20)

        # The skip is recorded in the PDF so staff can see the measurement was not taken.
        tk.Button(
            self.btn_frame,
            text="Tovább" if self.language == "hu" else "Next",
            font=("Arial", 24, "bold"),
            command=lambda: self.answer({
                "hu": "Nem mért (eszköz nem elérhető)",
                "en": "Not measured (device unavailable)",
            }),
        ).pack(pady=20)

    def show_button_question(self, q):
        """One large button that answers on press. No radio selection, no Tovább."""
        def press():
            button.configure(state="disabled")   # double-tap guard
            self.answer(q["value"])

        button = ctk.CTkButton(
            self.btn_frame,
            text=self.tr(q["label"]),
            font=("Arial", 30, "bold"),
            height=110,
            corner_radius=18,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["white"],
            command=press,
        )
        button.pack(fill="x", padx=60, pady=40)

    def poll_measurement(self):
        try:
            kind, payload = self.measure_queue.get_nowait()
        except queue.Empty:
            self.poll_job = self.after(200, self.poll_measurement)
            return

        print("poll_measurement: got", kind, payload, flush=True)

        self.poll_job = None
        self.measuring = False
        self.reset_timeout()

        if kind == "ok":
            self.answer(bp_answer(payload))
        else:
            print("poll_measurement: error:", repr(payload), flush=True)
            self.status.configure(text="A mérés nem sikerült. Kérjük, szóljon a személyzetnek.")
            tk.Button(
                self.btn_frame,
                text="Újra" if self.language == "hu" else "Retry",
                font=("Arial", 24, "bold"),
                command=self.show_question,
            ).pack(pady=20)

    