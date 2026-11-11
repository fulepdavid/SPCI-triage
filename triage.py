import customtkinter as ctk
from PIL import Image
from pathlib import Path
import logging

from config import CLOSING_MS, KIOSK, MOUSESYM_KEY, TIMEOUT_MS, resource_path
from content import APP
from device import BloodPressureDevice
from layout import LayoutMixin
from questions import QuestionMixin
from search import SearchMixin
from report import write_report
from theme import COLORS, FONTS
from hl7_listener import Hl7Listener

LOG_FILE = Path(__file__).resolve().parent / "kiosk.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

class App(LayoutMixin, QuestionMixin, SearchMixin, ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Triage")
        self.minsize(1024, 700)
        self.attributes("-fullscreen", True)
        self.configure(fg_color=COLORS["background"])

        # State. measuring must exist before reset_timeout() runs.
        self.session = {"answers": [], "index": 0}
        self.q_data = None
        self.current_node = None
        self.history = []
        self.language = None
        self.selected_option = None
        self.measuring = False
        self.timeout_job = None
        self.poll_job = None
        self.measure_queue = None
        self.closing_job = None
        self.reset_timeout()

        self.hl7 = Hl7Listener(KIOSK["hl7_host"], KIOSK["hl7_port"],
                               KIOSK["device_id"], allowed_ip=KIOSK["monitor_ip"])
        self.hl7.start()          # fails at startup if port 5000 is already in use

        self.bp = BloodPressureDevice(
            mouse_host=KIOSK["mouse_host"],
            mouse_port=KIOSK["mouse_port"],
            mouse_key=MOUSESYM_KEY,
            listener=self.hl7,
        )
       
        self.flag_hu = ctk.CTkImage(
            light_image=Image.open(resource_path("images/flags/flag_hu.png")), size=(64, 40))
        self.flag_us = ctk.CTkImage(
            light_image=Image.open(resource_path("images/flags/flag_us.png")), size=(64, 40))

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_header()
        self.container = ctk.CTkFrame(self, fg_color=COLORS["background"], corner_radius=0)
        self.container.grid(row=1, column=0, sticky="nsew")
        self.create_footer()


        self.bind_all("<Button>", lambda e: self.reset_timeout())
        self.bind_all("<Key>", lambda e: self.reset_timeout())

        self.show("LANGUAGE")

    # ---- navigation -----------------------------------------------------
    def show(self, node_id, save_history=True):
        if self.poll_job is not None:
            self.after_cancel(self.poll_job)
            self.poll_job = None
        if self.closing_job is not None:
            self.after_cancel(self.closing_job)
            self.closing_job = None
        self.measuring = False

        if node_id == "LANGUAGE":
            self.language = None
        if node_id in ("LANGUAGE", "CLOSING"):
            self.history.clear()
        elif save_history and self.current_node and self.current_node != node_id:
            self.history.append(self.current_node)

        self.current_node = node_id
        self.q_data = None
        self.selected_option = None

        for widget in self.container.winfo_children():
            widget.destroy()

        node = APP[node_id]
        frame = ctk.CTkFrame(self.container, fg_color=COLORS["background"], corner_radius=0)
        frame.pack(fill="both", expand=True)

        if node["type"] == "questionnaire":
            self.q_data = node
            self.session["index"] = 0
            self.session["answers"] = []
            self.session["questionnaire"] = {"id": node_id, "title": self.tr(node["title"])}
            self.create_questionnaire_layout(frame, node)
            self.show_question()

        elif node["type"] == "menu":
            ctk.CTkLabel(frame, text=self.tr(node["title"]), font=("Arial", 42, "bold"),
                         text_color=COLORS["heading"]).pack(pady=30)

            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(expand=True, fill="both", padx=60, pady=30)

            buttons = node["buttons"]
            cols = node.get("layout", {}).get("cols", 2)
            for c in range(cols):
                btn_frame.grid_columnconfigure(c, weight=1)
            for r in range((len(buttons) + cols - 1) // cols):
                btn_frame.grid_rowconfigure(r, weight=1)

            for i, (text, target) in enumerate(buttons):
                ctk.CTkButton(
                    btn_frame,
                    text=self.tr(text),
                    font=("Arial", 25, "bold"),
                    fg_color=COLORS["white"],
                    hover_color=COLORS["primary_light"],
                    text_color=COLORS["heading"],
                    border_width=1.5,
                    border_color=COLORS["border"],
                    corner_radius=18,
                    command=lambda t=target: self.show(t) if t else None,
                    state="normal" if target else "disabled",
                ).grid(row=i // cols, column=i % cols, sticky="nsew", padx=10, pady=10)

        elif node["type"] == "search":
            self.show_search(frame, node)

        elif node["type"] == "language":
            ctk.CTkLabel(frame, text=self.tr(node["title"]), font=FONTS["heading"],
                         text_color=COLORS["heading"]).pack(pady=(80, 40))

            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack()

            for label, flag, lang in (("Magyar", self.flag_hu, "hu"),
                                      ("English", self.flag_us, "en")):
                ctk.CTkButton(
                    row,
                    text=label,
                    image=flag,
                    font=("Arial", 26, "bold"),
                    width=320,
                    height=90,
                    fg_color=COLORS["white"],
                    hover_color=COLORS["primary_light"],
                    text_color=COLORS["heading"],
                    border_width=2,
                    border_color=COLORS["border"],
                    corner_radius=18,
                    command=lambda l=lang: self.set_language(l),
                ).pack(side="left", padx=15)

        elif node["type"] == "closing":
            self.create_closing_screen(frame, node)

        self.update_footer()
        self.reset_timeout()
        
    def go_back(self):
        if self.history:
            self.show(self.history.pop(), save_history=False)

    def set_language(self, lang):
        self.language = lang
        self.show("MAIN")

    def switch_language(self, lang):
        self.language = lang
        self.show(self.current_node, save_history=False)

    def show_help(self):
        pass

    def next_action(self):
        if self.q_data is None or self.selected_option is None:
            return
        value = self.selected_option
        self.selected_option = None
        self.answer(value)

    def create_closing_screen(self, frame, node):
        box = ctk.CTkFrame(frame, fg_color=COLORS["white"], border_width=1.5,
                           border_color=COLORS["border"], corner_radius=19)
        box.pack(expand=True, fill="both", padx=120, pady=40)

        for lang in ("hu", "en"):
            ctk.CTkLabel(box, text=node["title"][lang], font=FONTS["heading"],
                         text_color=COLORS["heading"]).pack(pady=(30, 5))
            ctk.CTkLabel(box, text=node["message"][lang], font=FONTS["subtitle"],
                         text_color=COLORS["text"], wraplength=900,
                         justify="center").pack(pady=(0, 20))
            if lang == "hu":
                ctk.CTkFrame(box, height=2, fg_color=COLORS["border"]).pack(
                    fill="x", padx=120, pady=10)

        ctk.CTkButton(
            box,
            text=f"{node['button']['hu']}  /  {node['button']['en']}",
            font=("Arial", 30, "bold"),
            height=100,
            corner_radius=18,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["white"],
            command=lambda: self.show("LANGUAGE"),
        ).pack(fill="x", padx=150, pady=40)

        self.closing_job = self.after(CLOSING_MS, lambda: self.show("LANGUAGE"))

    # ---- idle timeout ---------------------------------------------------
    def reset_timeout(self):
        if self.measuring:
            return
        if self.timeout_job is not None:
            self.after_cancel(self.timeout_job)
        self.timeout_job = self.after(TIMEOUT_MS, self.timeout)

    def timeout(self):
        self.language = None
        self.session["answers"] = []
        self.session["index"] = 0
        self.show("LANGUAGE")

    # ---- helpers --------------------------------------------------------
    def tr(self, value):
        if isinstance(value, dict):
            return value.get(self.language, value.get("en", next(iter(value.values()))))
        return value

    def finish_questionnaire(self):
        write_report(self.session["answers"], self.q_data["title"])
        self.send_data()
        self.show(self.q_data["end"], save_history=False)

    def send_data(self):
        pass  # hospital integration, not yet implemented

if __name__ == "__main__":
    App().mainloop()