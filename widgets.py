import tkinter as tk

HUNGARIAN_LAYOUT = [
    "0123456789ÖÜÓ",
    "QWERTZUIOPŐÚ",
    "ASDFGHJKLÉÁŰ",
    "ÍYXCVBNM,.-",
]
ENGLISH_LAYOUT = [
    "1234567890",
    "QWERTYUIOP",
    "ASDFGHJKL'",
    "ZXCVBNM.-",
]
NUMERIC_LAYOUT = [
    "123",
    "456",
    "789",
    "0",
]


class VirtualKeyboard(tk.Frame):
    def __init__(self, parent, search_callback=None, language="en", keyboard_type="normal"):
        super().__init__(parent)

        self.entry = None
        self.search_callback = search_callback
        self.language = language
        self.keyboard_type = keyboard_type
        is_numeric = keyboard_type in ("number", "date")

        if is_numeric:
            layout = NUMERIC_LAYOUT
        else:
            layout = HUNGARIAN_LAYOUT if language == "hu" else ENGLISH_LAYOUT
            s = bool(search_callback)
            if language == "hu":
                space_start, space_len = 0, 7 if s else 8
                back_start, back_len = (7 if s else 8), (3 if s else 5)
                search_start = 10
            else:
                space_start, space_len = 0, 6 if s else 7
                back_start, back_len = (6 if s else 7), (3 if s else 5)
                search_start = 9
            search_len = 3

        for r, row in enumerate(layout):
            for c, char in enumerate(row):
                column = 1 if (is_numeric and row == "0") else c
                tk.Button(
                    self,
                    text=char,
                    font=("Arial", 24, "bold"),
                    bd=5,
                    command=lambda ch=char: self.insert(ch),
                ).grid(row=r, column=column, sticky="nsew")

        for c in range(max(len(row) for row in layout)):
            self.grid_columnconfigure(c, weight=1)
        for r in range(len(layout)):
            self.grid_rowconfigure(r, weight=1)

        if not is_numeric:
            tk.Button(
                self,
                text="Space",
                font=("Arial", 24, "bold"),
                bd=5,
                command=lambda: self.insert(" "),
            ).grid(row=4, column=space_start, columnspan=space_len, sticky="nsew")

            tk.Button(
                self,
                text="⌫",
                font=("Arial", 24, "bold"),
                bd=5,
                command=self.backspace,
            ).grid(row=4, column=back_start, columnspan=back_len, sticky="nsew")

            if self.search_callback:
                tk.Button(
                    self,
                    text="Keresés" if language == "hu" else "Search",
                    font=("Arial", 24, "bold"),
                    bd=5,
                    command=self.search_callback,
                ).grid(row=4, column=search_start, columnspan=search_len, sticky="nsew")
        else:
            tk.Button(
                self,
                text="⌫",
                font=("Arial", 24, "bold"),
                bd=5,
                command=self.backspace,
            ).grid(row=3, column=2, sticky="nsew")

        self.grid_rowconfigure(4, weight=1)

    def insert(self, text):
        if not self.entry:
            return
        if self.keyboard_type == "date":
            if len(self.input_buffer) < 8:
                self.input_buffer += text
                self.update_display()
        else:
            self.entry.insert(tk.INSERT, text)

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