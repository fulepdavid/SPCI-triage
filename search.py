import tkinter as tk

import customtkinter as ctk

from content import APP
from theme import COLORS, FONTS, KEY, RADIUS, SIZES
from widgets import VirtualKeyboard


def _styled_button(parent, text, command, **overrides):
    """Same look as the keyboard keys, so buttons follow theme.py."""
    style = dict(
        font=("Arial", 25, "bold"),
        fg_color=COLORS["white"],
        hover_color=COLORS["primary_light"],
        text_color=COLORS["heading"],
        border_width=1.5,
        border_color=COLORS["border"],
        corner_radius=18,
    )
    style.update(overrides)
    return ctk.CTkButton(parent, text=text, command=command, **style)


class SearchMixin:
    """Keyword search over APP. The keyboard stays visible at the bottom of this screen."""

    def show_search(self, frame, node):
        cols = node.get("layout", {}).get("cols", 1)

        # Grid layout: row 0 = entry, row 1 = results (takes the free space), row 2 = keyboard.
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=0)

        entry = tk.Entry(frame, font=("Arial", 24))
        entry.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        results_frame = ctk.CTkFrame(frame, fg_color="transparent")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=20)

        def perform_search():
            term = entry.get().lower().strip()

            for w in results_frame.winfo_children():
                w.destroy()

            if not term:
                return  # an empty search shows nothing

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
                _styled_button(
                    results_frame,
                    title,
                    lambda t=target: self.show(t),
                ).grid(row=i // cols, column=i % cols, sticky="nsew", padx=10, pady=10)

        keyboard = VirtualKeyboard(frame, search_callback=perform_search, language=self.language)
        keyboard.entry = entry
        keyboard.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        entry.focus_set()