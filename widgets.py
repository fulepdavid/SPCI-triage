import tkinter as tk
import customtkinter as ctk

from theme import COLORS, FONTS, RADIUS, SIZES, KEY
from strings import STRINGS

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

BACK_SPAN = 3
SEARCH_SPAN = 3
DATE_LENGTH = 8


def format_date(digits):
    """'20241225' -> '2024.12.25', built up as digits are typed."""
    out = digits[:4]
    if len(digits) > 4:
        out += "." + digits[4:6]
    if len(digits) > 6:
        out += "." + digits[6:8]
    return out


def _key(parent, text, command, **overrides):
    style = dict(
        height=SIZES["key_height"],
        corner_radius=RADIUS["key"],
        fg_color="white",
        hover_color=KEY["hover"],
        text_color=KEY["text"],
        border_width=0,
        font=FONTS["key"],
    )
    style.update(overrides)
    return ctk.CTkButton(parent, text=text, command=command, **style)


class VirtualKeyboard(ctk.CTkFrame):
    def __init__(self, parent, search_callback=None, language="en", keyboard_type="normal"):
        super().__init__(parent, fg_color=KEY["fg"], corner_radius=RADIUS["card"])

        self._entry = None
        self.search_callback = search_callback
        self.language = language
        self.keyboard_type = keyboard_type
        self.input_buffer = ""

        self.is_numeric = keyboard_type in ("number", "date")
        if self.is_numeric:
            layout = NUMERIC_LAYOUT
        elif language == "hu":
            layout = HUNGARIAN_LAYOUT
        else:
            layout = ENGLISH_LAYOUT

        self.cols = max(len(row) for row in layout)
        pad = SIZES["key_pad"]
        bottom = len(layout)

        # Character keys, centered row by row
        for r, row in enumerate(layout):
            offset = (self.cols - len(row)) // 2
            for c, ch in enumerate(row):
                _key(self, ch, lambda ch=ch: self.insert(ch)).grid(
                    row=r, column=offset + c, sticky="nsew", padx=pad, pady=pad
                )

        if self.is_numeric:
            _key(self, "⌫", self.backspace).grid(
                row=bottom - 1, column=self.cols - 1, sticky="nsew", padx=pad, pady=pad
            )
            n_rows = len(layout)
        else:
            n_search = SEARCH_SPAN if search_callback else 0
            n_space = self.cols - BACK_SPAN - n_search
            space_text = STRINGS["space"].get(language, STRINGS["space"]["en"])

            _key(self, space_text, lambda: self.insert(" ")).grid(
                row=bottom, column=0, columnspan=n_space, sticky="nsew", padx=pad, pady=pad
            )
            _key(self, "⌫", self.backspace).grid(
                row=bottom, column=n_space, columnspan=BACK_SPAN, sticky="nsew", padx=pad, pady=pad
            )
            if search_callback:
                _key(
                    self,
                    "Keresés" if language == "hu" else "Search",
                    search_callback,
                    fg_color=COLORS["primary"],
                    hover_color=COLORS["primary_hover"],
                    text_color=COLORS["white"],
                ).grid(
                    row=bottom, column=n_space + BACK_SPAN, columnspan=SEARCH_SPAN,
                    sticky="nsew", padx=pad, pady=pad
                )
            n_rows = len(layout) + 1

        for c in range(self.cols):
            self.grid_columnconfigure(c, weight=1, uniform="keys")
        for r in range(n_rows):
            self.grid_rowconfigure(r, weight=1, uniform="keys")

    @property
    def entry(self):
        return self._entry

    @entry.setter
    def entry(self, widget):
        # Assigning the entry works the same as before. In date mode,
        # the buffer is seeded from whatever digits the entry already holds.
        self._entry = widget
        if widget is not None and self.keyboard_type == "date":
            digits = "".join(ch for ch in widget.get() if ch.isdigit())[:DATE_LENGTH]
            self.input_buffer = digits
            self._refresh_date()

    def insert(self, text):
        if self._entry is None:
            return
        if self.keyboard_type == "date":
            if text.isdigit() and len(self.input_buffer) < DATE_LENGTH:
                self.input_buffer += text
                self._refresh_date()
        else:
            # Appends at the end; the keyboard doesn't track caret position.
            self._entry.insert(tk.END, text)

    def backspace(self):
        if self._entry is None:
            return
        if self.keyboard_type == "date":
            self.input_buffer = self.input_buffer[:-1]
            self._refresh_date()
        else:
            value = self._entry.get()
            if value:
                self._entry.delete(len(value) - 1, tk.END)

    def _refresh_date(self):
        self._entry.delete(0, tk.END)
        self._entry.insert(0, format_date(self.input_buffer))

    def get_value(self):
        if self.keyboard_type == "date":
            return self.input_buffer
        return self._entry.get()