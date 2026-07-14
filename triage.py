import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime
import os
import sys
import random

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(
    TTFont("DejaVu", "fonts/DejaVuSans.ttf")
)

class VirtualKeyboard(tk.Frame):
    def __init__(self, parent, search_callback=None, language='en', keyboard_type="normal"):
        super().__init__(parent)

        self.entry = None
        self.search_callback=search_callback
        self.language = language
        self.keyboard_type = keyboard_type
        is_numeric = False
        if self.keyboard_type == "number" or self.keyboard_type == "date":
            is_numeric = True
        


        normal_layout = [
            "0123456789ÖÜÓ",
            "QWERTZUIOPŐÚ",
            "ASDFGHJKLÉÁŰ",
            "ÍYXCVBNM,.-"
        ]

        numeric_layout = [
            "123",
            "456",
            "789",
            "0"
        ]

        
        if is_numeric:
            layout=numeric_layout
        else: 
            layout=normal_layout
        

        for r, row in enumerate(layout):
            for c, char in enumerate(row):

                column = c

                if is_numeric and row == "0":
                    column = 1

                btn = tk.Button(
                    self,
                    text=char,
                    font=("Arial", 24, "bold"),
                    bd=5,
                    command=lambda ch=char: self.insert(ch)
                )

                btn.grid(
                    row=r,
                    column=column,
                    sticky="nsew"
        )
                
        for c in range(max(len(row) for row in layout)):
            self.grid_columnconfigure(c, weight=1)

        for r in range(len(layout)):
            self.grid_rowconfigure(r, weight=1)

        if not is_numeric: 
            space_btn = tk.Button(
                self,
                text="Space",
                font=("Arial", 24, "bold"),
                bd=5,
                command=lambda: self.insert(" ")
            )

            space_btn.grid(
                row=4,
                column=0,
                columnspan=7 if self.search_callback else 8,
                sticky="nsew"
            )

        backspace_btn = tk.Button(
            self,
            text="⌫",
            font=("Arial", 24, "bold"),
            bd=5,
            command=self.backspace
        )
        
        if is_numeric:
            backspace_btn.grid(
                row=3,
                column=2,
                sticky="nsew"
            )
        else:
            backspace_btn.grid(
                row=4,
                column=7 if self.search_callback else 8,
                columnspan=3 if search_callback else 5,
                sticky="nsew"
            )

        if self.search_callback:
            search_btn = tk.Button(
                self,
                text="Keresés" if self.language == 'hu' else 'Search',
                font=("Arial", 24, "bold"),
                bd=5,
                command=self.search_callback
            )

            search_btn.grid(
                row=4,
                column=10,
                columnspan=3,
                sticky="nsew"
            )

        self.grid_rowconfigure(4, weight=1)

    # def insert(self, text):
    #     if self.entry:
    #         self.entry.insert(tk.INSERT, text)

    def insert(self, text):
        if not self.entry:
            return

        if self.keyboard_type == "date":
            if len(self.input_buffer) < 8:
                self.input_buffer += text
                self.update_display()
        else:
            self.entry.insert(tk.INSERT, text)

    # def backspace(self):
    #     if not self.entry:
    #         return

    #     pos = self.entry.index(tk.INSERT)

    #     if pos > 0:
    #         self.entry.delete(pos - 1)

    def backspace(self):
        if not self.entry:
            return

        if self.keyboard_type == "date":
            self.input_buffer = self.input_buffer[:-1]
            self.update_display()
        else:
            pos = self.entry.index(tk.INSERT)

            if pos > 0:
                self.entry.delete(pos - 1)

    def update_display(self):
        text = self.input_buffer

        if len(text) > 4:
            text = text[:4] + "." + text[4:]

        if len(text) > 6:
            text = text[:7] + "." + text[7:]

        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def get_value(self):
        if self.keyboard_type == "date":
            return self.input_buffer

        return self.entry.get()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

TIMEOUT_MS = 3 * 60 * 1000  

NAME_QUESTION = {
    "type": "text",
    "keyboard_type": "normal",
    "text": {'hu': "Mi a neve?", "en": "Whats your name?"},
    "answer_label":{'hu': 'Beteg neve', 'en': 'Patient\'s name'},
    "error_label":{"hu": "Adja meg a nevét", "en": "Enter your name"},
    "placeholder": "Adja meg a nevét",
    "required": True
}

TAJSZAM_QUESTION = {
    "type": "text",
    "keyboard_type": "number",
    "text": {'hu': "Adja meg a TAJ számát", "en": "Input your TAJ number"},
    "answer_label":{'hu': 'Beteg TAJ száma', 'en': 'Patient\'s TAJ number'},
    "error_label":{"hu": "Adja meg a TAJ számát", "en": "Enter your TAJ number"},
    "placeholder": "Adja meg a TAJ számát",
    "required": True
}

EVSZAM_QUESTION = {
    "type": "text",
    "keyboard_type": "date",
    "text": {'hu': "Adja meg a születési dátumát", "en": "Input your date of birth"},
    "answer_label":{'hu': 'Beteg születési dátuma', 'en': 'Patient\'s date of birth'},
    "error_label":{"hu": "Adja meg a születési dátumát", "en": "Enter your date of birth"},
    "placeholder": "Adja meg a születési dátumát",
    "required": True
}

APP = {
    "LANGUAGE": {
        "title": "Select language / Nyelvválasztás",
        "type": "language"
    },

    "MAIN": {
        "title": {
            "hu":"Vezető panasz",
            "en":"Leading complaint"
        },
        "type": "menu",
        "layout": {
            "cols": 2
        },
        "hidden_from_search": True,
        "buttons": [
            ({'hu':"Fül-orr-gégészeti", 'en':'Ear, nose, and throat'}, "FULORRGEGESZET"),
            ({'hu':"Szemészeti", 'en':'Ophthalmology'}, None),
            ({'hu':'Légzési', 'en':'Respiratory'}, None),
            ({'hu':'Keringési', 'en':'Circulatory'}, None),
            ({'hu':'Sérülés', 'en':'Injury'}, None),
            ({'hu':'Idegrendszeri', 'en':'Neurological'}, None),
            ({'hu':'Hasi/Emésztési', 'en':'Abdominal/Digestive'}, None),
            ({'hu':'Nőgyógyászati', 'en':'Gynecological'}, None),
            ({'hu':'Fájdalom/Láz', 'en':'Pain/Fever'}, 'FAJDALOMLAZ_MENU'),
            ({'hu':'Mellkasi', 'en':'Chest'}, None),
            ({'hu':'Egyéb', 'en':'Other'}, None),
            ({'hu':'Keresés', 'en':'Search'}, "KERESES"),
        ]
    },

    "FULORRGEGESZET": {
        "title": {'hu':"Fül-orr-gégészet",'en':'ear, nose, and throat'},
        "type": "menu",
        "buttons": [
            ({'hu':"Orr",'en':'Nose'}, "ORR_MENU"),
            ({'hu': "Fül", 'en':'Ear'}, "FUL_MENU"),
            ({'hu': "Torok/Gége", 'en': "Throat/Larynx"}, None),
            ({'hu': 'Száj', 'en': 'Mouth'}, None),
            ({'hu': "Nyak", 'en': 'Neck'}, None)
        ],
        "keywords":{
            'hu':["fül", "orr", "gége", "teszt"],
            'en':['ear', 'nose', 'throat', 'test']
        }
    },

    "ORR_MENU": {
        "title": {'hu': "Orr", 'en': 'Nose'},
        "type": "menu",
        "buttons": [
            ({'hu': "Orrvérzés", 'en': 'Nose bleed'}, "ORR_VERZES"),
            ({'hu': "Orrdugulás, szénanátha", 'en': "Nasal congestion, hay fever"}, None),
            ({'hu': "Idegentest", 'en': "Foreign Body"}, None),
            ({'hu': "Felső légúti fertőzés", 'en': 'Upper respiratory infection'}, None),
            ({'hu': "Orr sérülés", 'en': 'Nose injury'}, None)
        ]
    },

    "ORR_VERZES": {
        "type": "questionnaire",
        "title": {'hu': "Orrvérzés", 'en': 'Nose bleed'},
        "questions": [
            {
                "type": "choice",
                "text": {'hu':"Orrvérzés 1",'en':'Nose bleed 1'},
                "layout": {
                    "cols": 1
                },
                "options": [{'hu': "Vérzékenység – Intenzíves kezelés korábban", 'en': 'Bleeding disorder – Previously treated in intensive care'}, {"hu": "Vérzékenység – Intenzíves kezelés nem volt", "en":"Bleeding disorder – Not previously treated in intensive care"}, {'hu': "Nincs vérzékenység", 'en': 'No bleeding disorder'}]
            },
            {
                "type": "choice",
                "text": {'hu':"Orrvérzés 2", 'en':'Nose bleed 2'},
                "layout": {
                    "cols": 2
                },
                "options": [{'hu': "Csillapíthatatlan / nyomásra sem csillapodó", 'en': 'Undamped / not dampened by pressure'}, {'hu':"Nyomásra csillapodó", 'en': 'Dampened by pressure'}, {'hu': "Jelenleg nem vérző – első/ritka orrvérzés", 'en': "Currently not bleeding – first/rare nosebleed"}, {'hu': "Jelenleg nem vérző - Visszatérő orrvérzés", 'en': "Currently not bleeding - Recurrent nosebleeds"}]
            },
            NAME_QUESTION,
            TAJSZAM_QUESTION,
            EVSZAM_QUESTION
        ],
        "end": "LANGUAGE"
    },

    "FUL_MENU":{
        "title":{'hu': "Fül", 'en':'Ear'},
        "type":"menu",
        "buttons":[
            ({'hu': "Fülfájás", 'en': 'Ear pain'}, None),
            ({'hu': "Idegentest a fülben", 'en': 'Foreign body in ear'}, None),
            ({'hu': "Hallásvesztés/Süketség", 'en': 'Hearing loss/Deafness'}, "HALLASVESZTES"),
            ({'hu': "Fülzúgás", 'en': 'Tinnitus'}, "FULZUGAS"),
            ({'hu': "Fülfolyás", 'en': 'Ear discharge'}, None),
            ({'hu': "Fül sérülés", 'en': 'Ear injury'}, None),
        ]
    },

    "HALLASVESZTES": {
        "type": "questionnaire",
        "title": {'hu': "Hallásvesztés/Süketség", 'en': 'Hearing loss/Deafness'},
        "questions": [
            {
                "type": "choice",
                "text": {'hu': "Hallásvesztés/Süketség", 'en': 'Hearing loss/Deafness'},
                "options": [{'hu': "Hirtelen kezdet", 'en': 'Sudden onset'}, {'hu': "Fokozatos kezdet", 'en': 'Gradual onset'}]
            },
        ],
        "end": "LANGUAGE"
    },

    "FULZUGAS": {
        "type": "questionnaire",
        "title": {'hu': "Fülzúgás", 'en': 'Tinnitus'},
        "questions": [
            {
                "type": "choice",
                "text": {'hu': "Fülzúgás", 'en': 'Tinnitus'},
                "options": [{'hu': "Nagy mennyiségű (4+ tbl/24 óra)Aspirint szedett be az elmúlt 48 órában?", 'en': 'Have you taken large amounts (4+ tablets/24 hours) of Aspirin in the past 48 hours?'}, {'hu': "Nem szedett Aspirint", 'en': 'Didn\'t take aspirin'}]
            },
        ],
        "end": "LANGUAGE"
    },
    "FAJDALOMLAZ_MENU":{
        "title":"Fájdalom/Láz",
        "type":"menu",
        "buttons":[
            ({'hu': "Fájdalom, sérülés nem érte", 'en': "Pain, no injury."}, None),
            ({'hu': "Fájdalom, sérülés nem érte és légszomj", 'en': "Pain, no injury, and shortness of breath"}, None),
            ({'hu': "Fájdalom, sérülés érte", "en": "Pain, suffered injury"}, "FAJDALOM"),
            ({'hu': "Fájdalom és Láz", 'en': 'Pain and fever'}, "LAZ"),
            ({'hu': "Láz", 'en': 'Fever'}, None),
        ]
    },
    "FAJDALOM": {
        "type": "questionnaire",
        "title": {'hu': "Fájdalom", 'en': 'Pain'},
        "questions": [
            {
                "type": "bodymap",
                "text": {'hu': "Hol fáj?", 'en': 'Where does it hurt?'},
                "images":[
                    {
                        "image": "images/untitled.png",
                        "image_position": [100, 50],
                        "regions":[
                            {
                                "name":"Fej első kép",
                                "rect":[100,25,208,135]
                            },
                            {
                               "name":"Jobb kar",
                                "rect":[27,180,86,390]
                            },
                            {
                                "name":"Jobb kéz",
                                "rect":[26,391,77,462]
                            }
                        ]
                    },
                    {
                        "image": "images/untitled.png",
                        "image_position": [1800, 50],
                        "regions":[
                            {
                                "name":"Fej másik kép",
                                "rect":[100,25,208,135]
                            }
                        ]
                    }
                ]
            }
        ],
        "end": "LANGUAGE"
    },
    "LAZ": {
        "type": "questionnaire",
        "title": {'hu': "Láz", 'en': 'Fever'},
        "questions": [
            {
                "type": "choice",
                "text": {'hu': "Mióta lázas?", 'en': 'How long have you had a fever?'},
                "options": [
                    {'hu': "Ma kezdődött", 'en' : 'Started today'},
                    {'hu': "1-3 napja", 'en' : '1-3 days'},
                    {'hu': "3 napnál régebben", 'en' : 'More than 3 days'}
                ]
            },
            {
                "type": "choice",
                "text": {'hu': "Hidegrázása van?", 'en': 'Do you have chills?'},
                "options": [
                    {'hu': "Igen", 'en': 'Yes'},
                    {'hu': "Nem", 'en': 'No'}
                ]
            },
            {
                "type": "measurement",
                "text": {'hu': "Kérem helyezze a kezét a hőmérőre.", 'en': 'Please place your hand on the thermometer'},
                "device": "thermometer"
            }, NAME_QUESTION
        ],
        "end": "LANGUAGE"
    },
    
    "KERESES": {
        "title": {'hu': "Keresés", 'en': 'Search'},
        "type": "search",
        "layout": {
            "cols": 2
        },
        "hidden_from_search": True
    }
}

SHOW_IMAGE_OVERLAY = True



class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Triage')
        #self.state("zoomed") #linuxon nem működik
        
        # style = ttk.Style()
        # style.configure('Test.TButton',font=("Arial",24))

        self.container = tk.Frame(self, bg="#123123")
        self.container.pack(fill="both", expand=True)
        #self.attributes('-fullscreen', True)

        self.current_frame = None
        self.session = {
            "answers": [],
            "index": 0
        }
        self.q_data = None

        self.timeout_job = None

        self.reset_timeout()

        self.language = None
        self.flag_hu = tk.PhotoImage(file=resource_path("images/flags/flag_hu.png")).subsample(4,4)
        self.flag_us = tk.PhotoImage(file=resource_path("images/flags/flag_us.png")).subsample(4,4)
        self.show("LANGUAGE")

        self.bind_all("<Button>", lambda e: self.reset_timeout())
        self.bind_all("<Key>", lambda e: self.reset_timeout())

    def set_language(self, lang):
        self.language = lang
        self.show("MAIN")

    def reset_timeout(self):
        if self.timeout_job is not None:
            self.after_cancel(self.timeout_job)

        self.timeout_job = self.after(
            TIMEOUT_MS,
            self.timeout
        )

    def timeout(self):
        self.language = None
        self.session["answers"] = []
        self.session["index"] = 0

        self.show("LANGUAGE")

    def tr(self, value):
        if isinstance(value, dict):
            return value.get(self.language, value.get("en", next(iter(value.values()))))
        return value
    
    def show(self, node_id):
        for w in self.container.winfo_children():
            w.destroy()

        node = APP[node_id]

        frame = tk.Frame(self.container)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text=self.tr(node["title"]), font=("Arial", 28))
        title.pack(pady=20)

        # menü(k)
        if node["type"] == "menu":
            btn_frame = tk.Frame(frame)
            btn_frame.pack(expand=True, fill="both")

            buttons = node["buttons"]

            cols = node.get("layout", {}).get("cols", 2)

            # configure grid to be responsive
            for r in range((len(buttons) + cols - 1) // cols):
                btn_frame.grid_rowconfigure(r, weight=1)

            for c in range(cols):
                btn_frame.grid_columnconfigure(c, weight=1)

            for i, (text, target) in enumerate(buttons):
                btn = tk.Button(
                    btn_frame,
                    text=self.tr(text),
                    font=('Arial',30, 'bold'),
                    relief='raised',
                    wraplength=400,
                    bd=10,
                    command=lambda t=target: self.show(t) if t else None,
                    state="active" if target else "disabled"
                )

                btn.grid(
                    row=i // cols,
                    column=i % cols,
                    sticky="nsew",
                    padx=10,
                    pady=10
                )

        # kérdőív(ek)
        elif node["type"] == "questionnaire":
            self.q_data = node
            self.session['index'] = 0
            self.session['answers'] = []


            self.session["questionnaire"] = {
                "id": node_id,
                "title": self.tr(node["title"])
            }

            self.q_frame = tk.Frame(frame)
            self.q_frame.pack(expand=True, fill="both")

            self.question_label = tk.Label(self.q_frame, font=("Arial", 30))
            self.question_label.pack(pady=30)

            self.btn_frame = tk.Frame(self.q_frame)
            self.btn_frame.pack(expand=True, fill="both")

            self.show_question()

        #keresés
        elif node["type"] == "search":
            entry = tk.Entry(
                frame,
                font=("Arial", 24)
            )
            entry.pack(fill="x", padx=20, pady=20)

            def perform_search():
                term = entry.get().lower().strip()

                keyboard.pack_forget()
                self.focus_set()

                for w in results_frame.winfo_children():
                    w.destroy()

                results = []

                for node_id, node in APP.items():

                    if node.get("hidden_from_search", False):
                        continue

                    title = node.get("title", "")

                    if isinstance(title, dict):
                        title = title.get(self.language, "")

                    searchable = [title]

                    searchable.extend(node.get("keywords", {}).get(self.language, []))

                    for text in searchable:
                        if term in text.lower():
                            results.append((title, node_id))
                            break

                cols = node.get("layout", {}).get("cols", 1)
                rows = (len(results) + cols - 1) // cols

                for r in range(rows):
                    results_frame.grid_rowconfigure(r, weight=1)

                for c in range(cols):
                    results_frame.grid_columnconfigure(c, weight=1)

                for i, (title, target) in enumerate(results):
                    tk.Button(
                        results_frame,
                        text=title,
                        font=('Arial',30, 'bold'),
                        relief='raised',
                        wraplength=400,
                        bd=10,
                        command=lambda t=target: self.show(t)
                    ).grid(
                        row=i // cols,
                        column=i % cols,
                        sticky="nsew",
                        padx=10,
                        pady=10
                    )

            def entry_focused(event):
                keyboard.entry = event.widget
                keyboard.input_buffer = ""

                if not keyboard.winfo_ismapped():
                    keyboard.pack(
                        side="bottom",
                        fill="x",
                        after=button_frame
                    )

            keyboard = VirtualKeyboard(frame, search_callback=perform_search, language=self.language)

            entry.bind("<FocusIn>", entry_focused)

            results_frame = tk.Frame(frame)
            results_frame.pack(fill="both", expand=True)

            button_frame = tk.Frame(frame)
            button_frame.pack(side="bottom", fill="both", pady=10)
            button_frame.grid_columnconfigure(0, weight=1)

            tk.Button(
                button_frame,
                text="Vissza" if self.language == 'hu' else 'Back',
                font=("Arial", 24, "bold"),
                bd=5,
                command=lambda: self.show("MAIN")
            ).pack(
                fill="x",
                expand=True,
                padx=10
            )

        elif node["type"] == "language":

            tk.Button(
                frame,
                image=self.flag_hu,
                text="Magyar",
                font=("Arial", 36, "bold"),
                compound="left",
                command=lambda: self.set_language("hu")
            ).pack(expand=True, fill="both", padx=50, pady=20)

            tk.Button(
                frame,
                image=self.flag_us,
                text="English",
                font=("Arial", 36, "bold"),
                compound="left",
                command=lambda: self.set_language("en")
            ).pack(expand=True, fill="both", padx=50, pady=20)
 
    def measure_device(self, device):
        if device == "thermometer":
            value = round(random.uniform(36.2, 39.5), 1)

        elif device == "pulse":
            value = random.randint(55, 120)

        else:
            value = None

        self.answer(value)

    def show_question(self):
        self.btn_frame.destroy()
        self.btn_frame = tk.Frame(self.q_frame)
        self.btn_frame.pack(expand=True, fill="both")

        questions = self.q_data["questions"]

        if self.session['index'] >= len(questions):
            self.finish_questionnaire()
            return

        q = questions[self.session['index']]
        self.question_label.config(text=self.tr(q["text"]))

        if q["type"] == "choice":
            self.show_choice_question(q)

        elif q["type"] == "bodymap":
            self.show_image_question(q)

        elif q["type"] == "measurement":
            self.show_measurement_question(q)
        
        elif q["type"] == "text":
           self.show_text_question(q)

    def show_choice_question(self, q):
        cols = q.get("layout", {}).get("cols", 1)

        options = q["options"]

        rows = (len(options) + cols - 1) // cols

        for r in range(rows):
            self.btn_frame.grid_rowconfigure(r, weight=1)

        for c in range(cols):
            self.btn_frame.grid_columnconfigure(c, weight=1)

        for i, opt in enumerate(options):
            text = self.tr(opt)
            tk.Button(
                self.btn_frame,
                text=text,
                font=("Arial", 30, "bold"),
                relief="raised",
                wraplength=400,
                bd=10,
                command=lambda o=opt: self.answer(o)
            ).grid(
                row=i // cols,
                column=i % cols,
                sticky="nsew",
                padx=10,
                pady=10
            )

    def show_image_question(self, q):
        self.canvas = tk.Canvas(self.btn_frame, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.images = []  

        for img_data in q["images"]:


            image = tk.PhotoImage(file=resource_path(img_data["image"]))
            self.images.append(image)

            x, y = img_data["image_position"]


            image_id = self.canvas.create_image(
                x,
                y,
                anchor="nw",
                image=image
            )

            if SHOW_IMAGE_OVERLAY:
                for region in img_data["regions"]:
                    x1, y1, x2, y2 = region["rect"]

                    rect = self.canvas.create_rectangle(
                        x + x1,
                        y + y1,
                        x + x2,
                        y + y2,
                        outline="red",
                        width=2
                    )
                    self.canvas.tag_bind(
                        rect,
                        "<Button-1>",
                        lambda e, data=img_data: self.image_click(e, data)
                    )

                    text = self.canvas.create_text(
                        x + (x1 + x2) / 2,
                        y + (y1 + y2) / 2,
                        text=region["name"]
                    )
                    self.canvas.tag_bind(
                        text,
                        "<Button-1>",
                        lambda e, data=img_data: self.image_click(e, data)
                    )

            self.canvas.tag_bind(
                image_id,
                "<Button-1>",
                lambda e, data=img_data: self.image_click(e, data)
            )

    def show_measurement_question(self, q):
        self.status = tk.Label(
            self.btn_frame,
            text="Mérés folyamatban...",
            font=("Arial", 20)
        )
        self.status.pack(pady=20)

        # kamu mérés amíg nincs eszköz
        tk.Button(
            self.btn_frame,
            text="Szimulált mérés",
            font=("Arial", 22),
            command=lambda: self.measure_device(q["device"])
        ).pack(pady=20)

    def show_text_question(self, q):

        self.error_label = tk.Label(
            self.btn_frame,
            text="",
            font=("Arial", 20),
            fg="red"
        )

        self.error_label.pack(pady=10)

        keyboard = VirtualKeyboard(
            self.btn_frame,
            language=self.language,
            keyboard_type=q['keyboard_type'],
        )


        entry = tk.Entry(
            self.btn_frame,
            font=("Arial", 24)
        )

        def entry_focused(event):
            keyboard.entry = event.widget
            keyboard.input_buffer = ""

            if not keyboard.winfo_ismapped():
                keyboard.pack(
                    side="bottom",
                    fill="x"
                )

        entry.bind("<FocusIn>", entry_focused)
        entry.bind("<Key>", lambda e: "break")

        entry.pack(
            fill="x",
            padx=50,
            pady=30
        )

        entry.focus_set()

        def submit():
            value = keyboard.get_value().strip()

            if q.get("required", False) and not value:
                self.error_label.config(
                    text=self.tr(q["error_label"])
                )
                return
            
            if q.get("keyboard_type") == "date":
                try:
                    datetime.strptime(value, "%Y%m%d")
                except ValueError:
                    self.error_label.config(
                        text="Please enter a valid date."
                    )
                    return

            self.error_label.config(text="")
            self.answer(value)

        tk.Button(
            self.btn_frame,
            text="Tovább" if self.language == 'hu' else 'Next',
            font=("Arial", 24, "bold"),
            command=submit
        ).pack(
            pady=20
    )

    def center_image(self, event):
        if not hasattr(self, "image_id"):
            return
        
        self.canvas.coords(
            self.image_id,
            event.width // 2,
            event.height // 2
        )

    def canvas_to_image_coords(self, x, y):
        img_x, img_y = self.canvas.coords(self.image_id)

        return (
            x - img_x,
            y - img_y
        )
        
            
    def image_click(self, event, image_data):
        img_x, img_y = image_data["image_position"]

        x = event.x - img_x
        y = event.y - img_y

        for region in image_data["regions"]:
            x1, y1, x2, y2 = region["rect"]

            if x1 <= x <= x2 and y1 <= y <= y2:
                self.answer(region["name"])
                return

    def answer(self, value):
        q = self.q_data["questions"][self.session['index']]
        label = q.get("answer_label", q["text"])

        self.session['answers'].append((self.tr(label), value))

        self.session['index'] += 1
        self.show_question()

    def finish_questionnaire(self):
        answers_dir = Path("answers")
        answers_dir.mkdir(exist_ok=True)

        filename = answers_dir / f"answers_{datetime.now():%Y%m%d_%H%M%S}.pdf"

        styles = getSampleStyleSheet()

        styles["Normal"].fontName = "DejaVu"
        styles["Heading1"].fontName = "DejaVu"
        styles["Heading2"].fontName = "DejaVu"
        styles["Title"].fontName = "DejaVu"

        doc = SimpleDocTemplate(str(filename))

        data = [
            ["Kérdés", "Válasz"]
        ]

        for q, a in self.session["answers"]:
            data.append([self.tr(q), self.tr(a)])
        
        table = Table(data, colWidths=[250, 250])

        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.black),

            ("GRID", (0,0), (-1,-1), 1, colors.black),

            ("FONTNAME", (0,0), (-1,0), "DejaVu"),
            ("FONTNAME", (0,1), (-1,-1), "DejaVu"),

            ("BOTTOMPADDING", (0,0), (-1,0), 12),

            ("VALIGN", (0,0), (-1,-1), "TOP"),

            ("BACKGROUND", (0,1), (-1,-1), colors.white),
        ]))

        story = []


        story.append(Paragraph("<b>Triage lap</b>", styles["Title"]))
        story.append(Spacer(1, 20))

        story.append(Paragraph(f"Dátum: {datetime.now():%Y-%m-%d %H:%M}", styles["Normal"]))
        story.append(Paragraph(f"Panasz: {self.tr(self.q_data['title'])}", styles["Normal"]))
        story.append(Spacer(1, 20))

        story.append(table)

        doc.build(story)


        self.language = None
        self.show(self.q_data["end"])

app = App()
app.mainloop()