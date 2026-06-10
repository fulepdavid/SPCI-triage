import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime


APP = {
    "MAIN": {
        "title": "Vezető panasz",
        "type": "menu",
        "layout": {
            "cols": 4
        },
        "buttons": [
            ("Fül-orr-gégészeti", "FULORRGEGESZET"),
            ("Szemészeti", None),
            ('Légzési', None),
            ('Keringési', None),
            ('Sérülés', None),
            ('Idegrendszeri', None),
            ('Hasi/Emésztési', None),
            ('Nőgyógyászati', None),
            ('Fájdalom/Láz', None),
            ('Mellkasi', None),
            ('Egyéb', None),
            ('Keresés', None),
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
                "options": ["Vérzékenység – Intenzíves kezelés korábban", "Vérzékenység – Intenzíves kezelés nem volt ", "Nincs vérzékenység"]
            },
            {
                "type": "choice",
                "text": "Orrvérzés 2",
                "options": ["Csillapíthatatlan / nyomásra sem csillapodó", "Nyomásra csillapodó", "Jelenleg nem vérző – első/ritka orrvérzés", "Jelenleg nem vérző - Visszatérő orrvérzés "]
            },
            {
                "type": "bodymap",
                "text": "Hol fáj?",
                "image": "images/untitled.png",
                "regions":[
                    {
                        "name":"Fej",
                        "rect":[100,25,208,135]
                    }
                ]
            }
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

    
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Triage')
        self.state("zoomed")

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

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
                    font=("Arial", 24),
                    command=lambda t=target: self.show(t) if t else None
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

            self.q_frame = tk.Frame(frame)
            self.q_frame.pack(expand=True, fill="both")

            self.question_label = tk.Label(self.q_frame, font=("Arial", 24))
            self.question_label.pack(pady=30)

            self.btn_frame = tk.Frame(self.q_frame)
            self.btn_frame.pack(expand=True, fill="both")

            self.show_question()
    
    def show_question(self):
        for w in self.btn_frame.winfo_children():
            w.destroy()

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
        for opt in q["options"]:
            tk.Button(
                self.btn_frame,
                text=opt,
                font=("Arial", 24),
                command=lambda o=opt: self.answer(o)
            ).pack(
                expand=True,
                fill="both",
                padx=10,
                pady=10
            )

    def show_image_question(self, q):
        self.canvas = tk.Canvas(self.btn_frame, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.body_image = tk.PhotoImage(file=q["image"])

        self.image_id = self.canvas.create_image(
            0,
            0,
            anchor="center",
            image=self.body_image
        )

        self.canvas.bind("<Configure>", self.center_image)
        self.canvas.tag_bind(
            self.image_id,
            "<Button-1>",
            lambda e, q=q: self.image_click(e, q)
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
        x_center, y_center = self.canvas.coords(self.image_id)

        img_width = self.body_image.width()
        img_height = self.body_image.height()

        image_x = x - (x_center - img_width / 2)
        image_y = y - (y_center - img_height / 2)

        return image_x, image_y

    def image_click(self, event, q):
        x, y = self.canvas_to_image_coords(
            event.x,
            event.y
        )

        for region in q["regions"]:
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
            for q, a in self.session['answers']:
                f.write(f"{q}: {a}\n")

        self.show(self.q_data["end"])

app = App()
app.mainloop()