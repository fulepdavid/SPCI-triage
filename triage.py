import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
            ('Fájdalom/Láz', 'FAJDALOM'),
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

            results_frame = tk.Frame(frame)
            results_frame.pack(fill="both", expand=True)

            def perform_search():
                term = entry.get().lower().strip()

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
                        bd=10,
                        command=lambda t=target: self.show(t)
                    ).grid(
                        row=i // cols,
                        column=i % cols,
                        sticky="nsew",
                        padx=10,
                        pady=10
                    )

            tk.Button(
                frame,
                text="Keresés",
                font=("Arial", 20),
                command=perform_search
            ).pack(pady=10)

            tk.Button(
                frame,
                text="Vissza",
                font=("Arial", 20),
                command=lambda: self.show("MAIN")
            ).pack(pady=10)
    
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

        filename = answers_dir / f"answers_{datetime.now():%Y%m%d_%H%M%S}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            #f.write(f"Kérdéssor: {self.session['questionnaire']}\n")
            for q, a in self.session['answers']:
                f.write(f"{q}: {a}\n")

        self.show(self.q_data["end"])

app = App()
app.mainloop()