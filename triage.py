import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime
import os
import sys
import random
import customtkinter as ctk
from PIL import Image


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(
    TTFont("DejaVu", "fonts/DejaVuSans.ttf")
)


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLORS = {
    "primary": "#087F7C",
    "primary_hover": "#066D6A",
    "primary_light": "#E8F5F3",
    "background": "#F3F7FA",
    "white": "#FFFFFF",
    "heading": "#17364D",
    "text": "#263F52",
    "secondary": "#617D93",
    "border": "#D3E1EB",
    "muted": "#A8BECE",
    "danger": "#D52D43",
}

FONTS = {
    "small": ("Arial", 13),
    "normal": ("Arial", 17),
    "body": ("Arial", 21),
    "subtitle": ("Arial", 22),
    "heading": ("Arial", 42, "bold"),
    "section": ("Arial", 19, "bold"),
    "button": ("Arial", 19, "bold"),
}

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
        


        hungarian_layout = [
            "0123456789ÖÜÓ",
            "QWERTZUIOPŐÚ",
            "ASDFGHJKLÉÁŰ",
            "ÍYXCVBNM,.-"
        ]

        english_layout = [
            "1234567890",
            "QWERTYUIOP",
            "ASDFGHJKL'",
            "ZXCVBNM.-"
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
            if language == 'hu':
                layout=hungarian_layout
                spacebar_start = 0
                spacebar_length = 7 if self.search_callback else 8
                backspace_start=7 if self.search_callback else 8
                backspace_length=3 if search_callback else 5
                search_start=10
                search_length=3
            else:
                layout=english_layout
                spacebar_start = 0
                spacebar_length = 6 if self.search_callback else 7
                backspace_start=6 if self.search_callback else 7
                backspace_length=3 if search_callback else 5
                search_start=9
                search_length=3
        

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
                column=spacebar_start,
                columnspan=spacebar_length,
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
                column=backspace_start,
                columnspan=backspace_length,
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
                column=search_start,
                columnspan=search_length,
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
    "id":'TAJSZAM',
    "type": "text",
    "keyboard_type": "number",
    "text": {'hu': "Adja meg a TAJ számát", "en": "Input your TAJ number"},
    "answer_label":{'hu': 'Beteg TAJ száma', 'en': 'Patient\'s TAJ number'},
    "error_label":{"hu": "Adja meg a TAJ számát (9 számjegy)", "en": "Enter your TAJ number (9 numbers)"},
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



class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Triage")
        self.minsize(1024, 700)

        self.attributes("-fullscreen", True)

        self.configure(fg_color=COLORS["background"])

        self.current_frame = None
        self.current_node = None
        self.history = []

        self.session = {
            "answers": [],
            "index": 0
        }

        self.q_data = None
        self.timeout_job = None
        self.language = None

        self.selected_option = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_header()

        self.container = ctk.CTkFrame(
            self,
            fg_color=COLORS["background"],
            corner_radius=0
        )
        self.container.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.create_footer()
        self.flag_hu = ctk.CTkImage(
            light_image=Image.open(resource_path("images/flags/flag_hu.png")),
            size=(64, 40)
        )

        self.flag_us = ctk.CTkImage(
            light_image=Image.open(resource_path("images/flags/flag_us.png")),
            size=(64, 40)
        )

        self.reset_timeout()

        self.bind_all("<Button>", lambda e: self.reset_timeout())
        self.bind_all("<Key>", lambda e: self.reset_timeout())

        self.show("LANGUAGE")


    def create_header(self):
        self.header = ctk.CTkFrame(
            self,
            height=80,
            fg_color=COLORS["white"],
            corner_radius=0
        )
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        self.header.grid_columnconfigure(0, weight=1)

        branding = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )
        branding.pack(side="left", padx=60, pady=15)

        logo_bar = ctk.CTkFrame(
            branding,
            width=10,
            height=44,
            fg_color=COLORS["primary"],
            corner_radius=0
        )
        logo_bar.pack(side="left", padx=(0, 12))
        logo_bar.pack_propagate(False)

        brand_text = ctk.CTkFrame(
            branding,
            fg_color="transparent"
        )
        brand_text.pack(side="left")

        ctk.CTkLabel(
            brand_text,
            text="Kórház neve",
            font=("Arial", 21, "bold"),
            text_color=COLORS["heading"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text,
            text="subtext",
            font=FONTS["small"],
            text_color=COLORS["text"]
        ).pack(anchor="w")

        right = ctk.CTkFrame(
            self.header,
            fg_color="transparent"
        )
        right.pack(side="right", padx=40)

        ctk.CTkLabel(
            right,
            text="BETEGOLDALI FELÜLET",
            font=("Arial", 14, "bold"),
            text_color=COLORS["primary"],
            fg_color=COLORS["primary_light"],
            corner_radius=20,
            width=285,
            height=40
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            right,
            text="TERV / DEMÓ",
            font=("Arial", 14, "bold"),
            text_color=COLORS["secondary"],
            fg_color=COLORS["background"],
            corner_radius=20,
            width=135,
            height=40
        ).pack(side="left", padx=8)

        self.top_progress = ctk.CTkFrame(
            self.header,
            height=6,
            fg_color="#E7EFF4",
            corner_radius=0
        )

        self.top_progress.place(
            relx=0,
            rely=1,
            anchor="sw",
            relwidth=1,
        )

        self.top_progress_bar = ctk.CTkFrame(
            self.top_progress,
            fg_color=COLORS["primary"],
            corner_radius=0
        )

        self.top_progress_bar.place(
            relx=0,
            rely=0,
            relheight=1,
            relwidth=0.26
        )

    def create_footer(self):
        self.footer = ctk.CTkFrame(
            self,
            height=94,
            fg_color=COLORS["white"],
            corner_radius=0,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.footer.grid(row=2, column=0, sticky="ew")
        self.footer.grid_propagate(False)

        self.footer.grid_columnconfigure(2, weight=1)

        self.back_button = ctk.CTkButton(
            self.footer,
            text="←  Vissza",
            width=180,
            height=60,
            font=FONTS["normal"],
            fg_color=COLORS["white"],
            hover_color=COLORS["background"],
            text_color=COLORS["text"],
            border_width=1.5,
            border_color=COLORS["border"],
            corner_radius=17,
            command=self.go_back
        )
        self.back_button.grid(
            row=0, column=0,
            padx=(65, 10), pady=16
        )

        self.home_button = ctk.CTkButton(
            self.footer,
            text="⌂  Főoldal",
            width=195,
            height=60,
            font=FONTS["normal"],
            fg_color=COLORS["white"],
            hover_color=COLORS["background"],
            text_color=COLORS["text"],
            border_width=1.5,
            border_color=COLORS["border"],
            corner_radius=17,
            command=lambda: self.show("MAIN")
        )
        self.home_button.grid(
            row=0, column=1,
            padx=0, pady=16
        )

        self.step_label = ctk.CTkLabel(
            self.footer,
            text="",
            font=("Arial", 19, "bold"),
            text_color=COLORS["secondary"]
        )
        self.step_label.grid(row=0, column=2, padx=25)

        self.time_label = ctk.CTkLabel(
            self.footer,
            text="Eltelt idő  00:00  ·  demonstráció",
            font=FONTS["normal"],
            text_color=COLORS["secondary"]
        )
        self.time_label.grid(row=0, column=3, padx=20)

        self.help_button = ctk.CTkButton(
            self.footer,
            text="Segítséget kérek",
            width=210,
            height=60,
            font=FONTS["normal"],
            fg_color=COLORS["white"],
            hover_color="#FFF0F1",
            text_color=COLORS["danger"],
            border_width=1.5,
            border_color=COLORS["border"],
            corner_radius=17,
            command=self.show_help
        )
        self.help_button.grid(
            row=0, column=4,
            padx=10, pady=16
        )

        self.next_button = ctk.CTkButton(
            self.footer,
            text="Tovább  →",
            width=190,
            height=66,
            font=("Arial", 21, "bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            text_color=COLORS["white"],
            corner_radius=17,
            command=self.next_action
        )
        self.next_button.grid(
            row=0, column=5,
            padx=(10, 65), pady=14
        )



    def go_back(self):
        if self.history:
            previous = self.history.pop()
            self.show(previous, save_history=False)


    def show_help(self):
        pass


    def next_action(self):
        if self.q_data is None:
            return

        if self.selected_option is not None:
            value = self.selected_option
            self.selected_option = None
            self.answer(value)


    def update_footer(self):
        if self.q_data is not None:

            questions = self.q_data["questions"]
            current = self.session["index"]

            self.step_label.configure(
                text=f"Lépés  {current + 1} / {len(questions)}"
            )

        else:
            self.step_label.configure(text="")

        is_choice = (
            self.q_data is not None
            and self.session["index"] < len(self.q_data["questions"])
            and self.q_data["questions"][self.session["index"]]["type"] == "choice"
        )

        self.next_button.configure(
            state="normal" if is_choice else "disabled"
        )


    def create_questionnaire_layout(self, frame, node):
        content = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )
        content.pack(
            fill="both",
            expand=True,
            padx=75,
            pady=(25, 35)
        )
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)

        content.grid_rowconfigure(0, weight=0)
        content.grid_rowconfigure(1, weight=0)
        content.grid_rowconfigure(2, weight=0)
        content.grid_rowconfigure(3, weight=1)

        content.grid_rowconfigure(1, weight=1)

        section = ctk.CTkLabel(
            content,
            text=self.tr(node.get("section", node["title"])).upper(),
            font=FONTS["section"],
            text_color=COLORS["primary"]
        )
        section.grid(
            row=0, column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 20)
        )

        self.q_frame = ctk.CTkFrame(
            content,
            fg_color=COLORS["white"],
            border_width=1.5,
            border_color=COLORS["border"],
            corner_radius=19
        )
        
        self.q_frame.grid(
            row=3, column=0,
            sticky="nsew",
            padx=(0, 38)
        )

        self.q_frame.grid_columnconfigure(0, weight=1)
        self.q_frame.grid_rowconfigure(1, weight=1)

        self.question_label = ctk.CTkLabel(
            content,
            text="",
            font=FONTS["heading"],
            text_color=COLORS["heading"],
            anchor="w",
            justify="left",
            wraplength=900
        )

        self.question_label.grid(
            row=1, column=0,
            sticky="w",
            pady=(0, 5)
        )

        self.subtitle_label = ctk.CTkLabel(
            content,
            text=self.tr(
                node.get(
                    "subtitle",
                    "Kérjük, válaszoljon az alábbi kérdésre."
                )
            ),
            font=FONTS["subtitle"],
            text_color=COLORS["secondary"],
            anchor="w"
        )

        self.subtitle_label.grid(
            row=2, column=0,
            sticky="w",
            pady=(0, 20)
        )

        self.info_panel = ctk.CTkFrame(
            content,
            fg_color=COLORS["primary_light"],
            border_width=1.5,
            border_color="#C8E7E3",
            corner_radius=19
        )
        self.info_panel.grid(
            row=3, column=1,
            sticky="nsew"
        )

        self.info_panel.grid_columnconfigure(0, weight=1)

        info_title = ctk.CTkLabel(
            self.info_panel,
            text=self.tr(
                node.get("info_title", "Mi történik ezután?")
            ),
            font=("Arial", 29, "bold"),
            text_color=COLORS["heading"],
            anchor="w"
        )
        info_title.pack(
            anchor="w",
            padx=40,
            pady=(45, 35)
        )

        info_text = ctk.CTkLabel(
            self.info_panel,
            text=self.tr(
                node.get(
                    "info_text",
                    "A következő lépésben további információkat kérdezünk."
                )
            ),
            font=("Arial", 22),
            text_color=COLORS["text"],
            anchor="nw",
            justify="left",
            wraplength=400
        )
        info_text.pack(
            anchor="w",
            fill="x",
            padx=40
        )

        info_badge = ctk.CTkLabel(
            self.info_panel,
            text=self.tr(
                node.get(
                    "info_badge",
                    "További információ"
                )
            ),
            font=("Arial", 15, "bold"),
            text_color=COLORS["primary"],
            fg_color=COLORS["white"],
            corner_radius=15,
            height=40
        )
        info_badge.pack(
            side="bottom",
            fill="x",
            padx=40,
            pady=55
        )

        self.btn_frame = ctk.CTkFrame(
            self.q_frame,
            fg_color="transparent"
        )
        self.btn_frame.pack(
            fill="both",
            expand=True,
            padx=42,
            pady=35
        )


    def show(self, node_id, save_history=True):
        if save_history and self.current_node and self.current_node != node_id:
            self.history.append(self.current_node)

        self.current_node = node_id
        self.q_data = None
        self.selected_option = None

        for widget in self.container.winfo_children():
            widget.destroy()

        node = APP[node_id]

        frame = ctk.CTkFrame(
            self.container,
            fg_color=COLORS["background"],
            corner_radius=0
        )
        frame.pack(fill="both", expand=True)

        if node["type"] == "questionnaire":
            self.q_data = node

            self.session["index"] = 0
            self.session["answers"] = []

            self.session["questionnaire"] = {
                "id": node_id,
                "title": self.tr(node["title"])
            }

            self.create_questionnaire_layout(frame, node)
            self.show_question()

        elif node["type"] == "menu":
            title = ctk.CTkLabel(
                frame,
                text=self.tr(node["title"]),
                font=FONTS["heading"],
                text_color=COLORS["heading"]
            )
            title.pack(pady=30)

            btn_frame = ctk.CTkFrame(
                frame,
                fg_color="transparent"
            )
            btn_frame.pack(
                expand=True,
                fill="both",
                padx=60,
                pady=30
            )

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
                    state="normal" if target else "disabled"
                ).grid(
                    row=i // cols,
                    column=i % cols,
                    sticky="nsew",
                    padx=10,
                    pady=10
                )

        elif node["type"] == "language":
            title = ctk.CTkLabel(
                frame,
                text=self.tr(node["title"]),
                font=FONTS["heading"],
                text_color=COLORS["heading"]
            )
            title.pack(pady=40)

            ctk.CTkButton(
                frame,
                text="Magyar",
                image=self.flag_hu,
                font=("Arial", 30, "bold"),
                fg_color=COLORS["white"],
                hover_color=COLORS["primary_light"],
                text_color=COLORS["heading"],
                border_width=2,
                border_color=COLORS["border"],
                corner_radius=18,
                command=lambda: self.set_language("hu"),
                height=100
            ).pack(
                expand=True,
                fill="x",
                padx=150,
                pady=15
            )

            ctk.CTkButton(
                frame,
                text="English",
                image=self.flag_us,
                font=("Arial", 30, "bold"),
                fg_color=COLORS["white"],
                hover_color=COLORS["primary_light"],
                text_color=COLORS["heading"],
                border_width=2,
                border_color=COLORS["border"],
                corner_radius=18,
                command=lambda: self.set_language("en"),
                height=100
            ).pack(
                expand=True,
                fill="x",
                padx=150,
                pady=15
            )
        self.update_footer()

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

            option_text = self.tr(opt)

            card = ctk.CTkFrame(
                self.btn_frame,
                fg_color=COLORS["white"],
                border_width=1.5,
                border_color=COLORS["border"],
                corner_radius=14,
                height=98
            )

            card.grid(
                row=i // cols,
                column=i % cols,
                sticky="nsew",
                padx=8,
                pady=8
            )

            card.grid_propagate(False)

            radio = ctk.CTkRadioButton(
                card,
                text=option_text,
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
                command=lambda o=opt, idx=i: self.select_option(o, idx)
            )

            radio.pack(
                fill="both",
                expand=True,
                padx=20
            )

            card.bind(
                "<Button-1>",
                lambda e, r=radio: r.invoke()
            )

            self.choice_widgets.append(card)


    def select_option(self, option, index):

        self.selected_option = option

        for i, card in enumerate(self.choice_widgets):

            if i == index:
                card.configure(
                    border_color=COLORS["primary"],
                    fg_color=COLORS["primary_light"]
                )
            else:
                card.configure(
                    border_color=COLORS["border"],
                    fg_color=COLORS["white"]
                )

        self.next_button.configure(state="normal")

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

        q = self.q_data["questions"][self.session['index']]

        self.selected_option = None

        self.question_label.configure(
            text=self.tr(q["text"])
        )

        self.update_footer()

        

        q = questions[self.session['index']]
        self.question_label.configure(text=self.tr(q["text"]))

        if q["type"] == "choice":
            self.show_choice_question(q)

        elif q["type"] == "bodymap":
            self.show_image_question(q)

        elif q["type"] == "measurement":
            self.show_measurement_question(q)
        
        elif q["type"] == "text":
           self.show_text_question(q)

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
                self.error_label.configure(
                    text=self.tr(q["error_label"])
                )
                return
            
            if q.get("id", None) == 'TAJSZAM' and len(value) != 9:
                self.error_label.configure(
                    text=self.tr(q["error_label"])
                )
                return
            
            if q.get("keyboard_type") == "date":
                try:
                    datetime.strptime(value, "%Y%m%d")
                except ValueError:
                    self.error_label.configure(
                        text="Please enter a valid date."
                    )
                    return
            

            self.error_label.configure(text="")
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

        #self.session['answers'].append((self.tr(label), value))

        self.session["answers"].append({
            #"question_id": question_id,
            "question": label,
            "answer": value
        })

        self.session['index'] += 1
        self.show_question()


    def generate_pdf(self):
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

        for answer in self.session["answers"]:
            q = answer['question']
            a = answer['answer']
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


    #kórházi rendszerbe adat küldés HA lesz
    def send_data(self):
        pass

    def finish_questionnaire(self):
        self.generate_pdf()
        self.send_data()

        self.language = None
        self.show(self.q_data["end"])

app = App()
app.mainloop()