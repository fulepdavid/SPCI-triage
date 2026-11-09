import tkinter as tk

import customtkinter as ctk

from content import APP
from theme import COLORS, FONTS
from widgets import VirtualKeyboard


class SearchMixin:
    """Keyword search over APP. Each result is a button that opens its screen."""

    def show_search(self, frame, node):
        cols = node.get("layout", {}).get("cols", 1)

        entry = tk.Entry(frame, font=("Arial", 24))
        entry.pack(fill="x", padx=20, pady=20)

        results_frame = ctk.CTkFrame(frame, fg_color="transparent")
        results_frame.pack(fill="both", expand=True, padx=20)

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(side="bottom", fill="x", pady=10, padx=20)

        def perform_search():
            term = entry.get().lower().strip()

            keyboard.pack_forget()
            self.focus_set()

            for w in results_frame.winfo_children():
                w.destroy()

            if not term:
                return  # an empty search shows nothing instead of all screens

            matches = []
            for node_id, candidate in APP.items():
                if candidate.get("hidden_from_search") or candidate["type"] in ("language", "search"):
                    continue
                title = self.tr(candidate.get("title", ""))
                keywords = candidate.get("keywords", {}).get(self.language, [])
                if any(term in text.lower() for text in [title, *keywords]):
                    matches.append((title, node_id))

            if not matches:
                ctk.CTkLabel(
                    results_frame,
                    text="Nincs találat" if self.language == "hu" else "No results",
                    font=FONTS["body"],
                    text_color=COLORS["secondary"],
                ).pack(pady=30)
                return

            rows = (len(matches) + cols - 1) // cols
            for r in range(rows):
                results_frame.grid_rowconfigure(r, weight=1)
            for c in range(cols):
                results_frame.grid_columnconfigure(c, weight=1)

            for i, (title, target) in enumerate(matches):
                tk.Button(
                    results_frame,
                    text=title,
                    font=("Arial", 30, "bold"),
                    relief="raised",
                    wraplength=400,
                    bd=10,
                    command=lambda t=target: self.show(t),
                ).grid(row=i // cols, column=i % cols, sticky="nsew", padx=10, pady=10)

        def entry_focused(event):
            keyboard.entry = event.widget
            keyboard.input_buffer = ""
            if not keyboard.winfo_ismapped():
                keyboard.pack(side="bottom", fill="x", after=button_frame)

        entry.bind("<FocusIn>", entry_focused)

        # Created after perform_search, which it receives as its search_callback.
        keyboard = VirtualKeyboard(frame, search_callback=perform_search, language=self.language)

        tk.Button(
            button_frame,
            text="Vissza" if self.language == "hu" else "Back",
            font=("Arial", 24, "bold"),
            bd=5,
            command=lambda: self.show("MAIN"),
        ).pack(fill="x", padx=10)