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
    def __init__(self, parent, search_callback=None):
        super().__init__(parent)

        self.entry = None
        self.search_callback=search_callback


        layout = [
            "0123456789ÖÜÓ",
            "QWERTZUIOPŐÚ",
            "ASDFGHJKLÉÁŰ",
            "ÍYXCVBNM,.-"
        ]

        for r, row in enumerate(layout):
            for c, char in enumerate(row):
                btn = tk.Button(
                    self,
                    text=char,
                    font=("Arial", 24, "bold"),
                    bd=5,
                    command=lambda ch=char: self.insert(ch)
                )

                btn.grid(
                    row=r,
                    column=c,
                    sticky="nsew"
        )
                
        for c in range(max(len(row) for row in layout)):
            self.grid_columnconfigure(c, weight=1)

        for r in range(len(layout)):
            self.grid_rowconfigure(r, weight=1)


        space_btn = tk.Button(
            self,
            text="Space",
            font=("Arial", 24, "bold"),
            bd=5,
            command=lambda: self.insert(" ")
        )

        backspace_btn = tk.Button(
            self,
            text="⌫",
            font=("Arial", 24, "bold"),
            bd=5,
            command=self.backspace
        )

        search_btn = tk.Button(
            self,
            text="Keresés",
            font=("Arial", 24, "bold"),
            bd=5,
            command=self.search_callback
        )

        space_btn.grid(
            row=4,
            column=0,
            columnspan=7,
            sticky="nsew"
        )

        backspace_btn.grid(
            row=4,
            column=7,
            columnspan=3,
            sticky="nsew"
        )

        search_btn.grid(
            row=4,
            column=10,
            columnspan=3,
            sticky="nsew"
        )

        self.grid_rowconfigure(4, weight=1)

    def insert(self, text):
        if self.entry:
            self.entry.insert(tk.INSERT, text)

    def backspace(self):
        if not self.entry:
            return

        pos = self.entry.index(tk.INSERT)

        if pos > 0:
            self.entry.delete(pos - 1)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def show_keyboard(event):
    parent = event.widget.winfo_toplevel()

    if not hasattr(parent, "_keyboard") or \
       not parent._keyboard.winfo_exists():

        parent._keyboard = VirtualKeyboard(
            parent,
            event.widget
        )
    else:
        parent._keyboard.entry = event.widget

APP = {
    "MAIN": {
        "title": "Vezető panasz",
        "type": "menu",
        "layout": {
            "cols": 2
        },
        "hidden_from_search": True,
        "buttons": [
            ("Fül-orr-gégészeti", "FULORRGEGESZET"),
            ("Szemészeti", None),
            ('Légzési', None),
            ('Keringési', None),
            ('Sérülés', None),
            ('Idegrendszeri', None),
            ('Hasi/Emésztési', None),
            ('Nőgyógyászati', None),
            ('Fájdalom/Láz', 'FAJDALOMLAZ_MENU'),
            ('Mellkasi', None),
            ('Egyéb', None),
            ('Keresés', "KERESES"),
        ]
    },

    "FULORRGEGESZET": {
        "title": "Fül-orr-gégészet",
        "type": "menu",
        "buttons": [
            ("Orr", "ORR_MENU"),
            ("Fül", "FUL_MENU"),
            ("Torok/Gége", None),
            ("Száj", None),
            ("Nyak", None)
        ],
        "keywords":[
            "fül",
            "orr",
            "gége",
            "teszt"
        ]
    },

    "ORR_MENU": {
        "title": "Orr",
        "type": "menu",
        "buttons": [
            ("Orrvérzés", "ORR_VERZES"),
            ("Orrdugulás, szénanátha", None),
            ("Idegentest", None),
            ("Felső légúti fertőzés", None),
            ("Orr sérülés", None)
        ]
    },

    "ORR_VERZES": {
        "type": "questionnaire",
        "title": "Orrvérzés",
        "questions": [
            {
                "type": "choice",
                "text": "Orrvérzés 1",
                "layout": {
                    "cols": 1
                },
                "options": ["Vérzékenység – Intenzíves kezelés korábban", "Vérzékenység – Intenzíves kezelés nem volt ", "Nincs vérzékenység"]
            },
            {
                "type": "choice",
                "text": "Orrvérzés 2",
                "layout": {
                    "cols": 2
                },
                "options": ["Csillapíthatatlan / nyomásra sem csillapodó", "Nyomásra csillapodó", "Jelenleg nem vérző – első/ritka orrvérzés", "Jelenleg nem vérző - Visszatérő orrvérzés "]
            },
        ],
        "end": "MAIN"
    },

    "FUL_MENU":{
        "title":"Fül",
        "type":"menu",
        "buttons":[
            ("Fülfájás", None),
            ("Idegentest a fülben", None),
            ("Hallásvesztés/Süketség", "HALLASVESZTES"),
            ("Fülzúgás", "FULZUGAS"),
            ("Fülfolyás", None),
            ("Fül sérülés", None),
        ]
    },

    "HALLASVESZTES": {
        "type": "questionnaire",
        "title": "Hallásvesztés/Süketség",
        "questions": [
            {
                "type": "choice",
                "text": "Hallásvesztés/Süketség",
                "options": ["Hirtelen kezdet", "Fokozatos kezdet"]
            },
        ],
        "end": "MAIN"
    },

    "FULZUGAS": {
        "type": "questionnaire",
        "title": "Fülzúgás",
        "questions": [
            {
                "type": "choice",
                "text": "Hallásvesztés/Süketség",
                "options": ["Nagy mennyiségű (4+ tbl/24 óra)Aspirint szedett be az elmúlt 48 órában?", "Nem szedett Aspirint"]
            },
        ],
        "end": "MAIN"
    },
    "FAJDALOMLAZ_MENU":{
        "title":"Fájdalom/Láz",
        "type":"menu",
        "buttons":[
            ("Fájdalom sérülés nem érte", None),
            ("Fájdalom sérülés nem érte és légszomj", None),
            ("Fájdalom sérülés érte", "FAJDALOM"),
            ("Fájdalom és Láz", "LAZ"),
            ("Láz", None),
        ]
    },
    "FAJDALOM": {
        "type": "questionnaire",
        "title": "Fájdalom",
        "questions": [
            {
                "type": "bodymap",
                "text": "Hol fáj?",
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
        "end": "MAIN"
    },
    "LAZ": {
        "type": "questionnaire",
        "title": "Láz",
        "questions": [
            {
                "type": "choice",
                "text": "Mióta lázas?",
                "options": [
                    "Ma kezdődött",
                    "1-3 napja",
                    "3 napnál régebben"
                ]
            },
            {
                "type": "choice",
                "text": "Hidegrázása van?",
                "options": [
                    "Igen",
                    "Nem"
                ]
            },
            {
                "type": "measurement",
                "text": "Kérem helyezze a kezét a hőmérőre.",
                "device": "thermometer"
            }
        ],
        "end": "MAIN"
    },
    
    "KERESES": {
        "title": "Keresés",
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

        self.show("MAIN")
    
    def show(self, node_id):
        for w in self.container.winfo_children():
            w.destroy()

        node = APP[node_id]

        frame = tk.Frame(self.container)
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text=node["title"], font=("Arial", 28))
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
                    text=text,
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

            #self.session["questionnaire"] = node["title"]

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

                    searchable = [
                        node.get("title", "")
                    ]

                    searchable.extend(
                        node.get("keywords", [])
                    )

                    for text in searchable:
                        if term in text.lower():
                            results.append(
                                (node["title"], node_id)
                            )
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

                if not keyboard.winfo_ismapped():
                    keyboard.pack(
                        side="bottom",
                        fill="x",
                        after=button_frame
                    )

            keyboard = VirtualKeyboard(frame, search_callback=perform_search)

            entry.bind("<FocusIn>", entry_focused)

            results_frame = tk.Frame(frame)
            results_frame.pack(fill="both", expand=True)

            button_frame = tk.Frame(frame)
            button_frame.pack(side="bottom", fill="both", pady=10)
            button_frame.grid_columnconfigure(0, weight=1)

            tk.Button(
                button_frame,
                text="Vissza",
                font=("Arial", 24, "bold"),
                bd=5,
                command=lambda: self.show("MAIN")
            ).pack(
                fill="x",
                expand=True,
                padx=10
            )
 
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
        self.question_label.config(text=q["text"])

        if q["type"] == "choice":
            self.show_choice_question(q)

        elif q["type"] == "bodymap":
            self.show_image_question(q)

        elif q["type"] == "measurement":
            self.show_measurement_question(q)

    def show_choice_question(self, q):
        cols = q.get("layout", {}).get("cols", 1)

        options = q["options"]

        rows = (len(options) + cols - 1) // cols

        for r in range(rows):
            self.btn_frame.grid_rowconfigure(r, weight=1)

        for c in range(cols):
            self.btn_frame.grid_columnconfigure(c, weight=1)

        for i, opt in enumerate(options):
            tk.Button(
                self.btn_frame,
                text=opt,
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
        self.session['answers'].append((q["text"], value))

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
            data.append([q, a])
        
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
        story.append(Paragraph(f"Panasz: {self.q_data['title']}", styles["Normal"]))
        story.append(Spacer(1, 20))

        story.append(table)

        doc.build(story)

        self.show(self.q_data["end"])

app = App()
app.mainloop()