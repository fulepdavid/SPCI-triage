import customtkinter as ctk

from theme import COLORS, FONTS


class LayoutMixin:
    """Builds the fixed parts of the screen: header, footer and questionnaire frame."""

    def create_header(self):
        self.header = ctk.CTkFrame(self, height=80, fg_color=COLORS["white"], corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)
        self.header.grid_columnconfigure(0, weight=1)

        branding = ctk.CTkFrame(self.header, fg_color="transparent")
        branding.pack(side="left", padx=60, pady=15)

        logo_bar = ctk.CTkFrame(branding, width=10, height=44, fg_color=COLORS["primary"], corner_radius=0)
        logo_bar.pack(side="left", padx=(0, 12))
        logo_bar.pack_propagate(False)

        brand_text = ctk.CTkFrame(branding, fg_color="transparent")
        brand_text.pack(side="left")
        ctk.CTkLabel(brand_text, text="Kórház neve", font=("Arial", 21, "bold"),
                     text_color=COLORS["heading"]).pack(anchor="w")
        ctk.CTkLabel(brand_text, text="subtext", font=FONTS["small"],
                     text_color=COLORS["text"]).pack(anchor="w")

        right = ctk.CTkFrame(self.header, fg_color="transparent")
        right.pack(side="right", padx=40)
        ctk.CTkLabel(right, text="BETEGOLDALI FELÜLET", font=("Arial", 14, "bold"),
                     text_color=COLORS["primary"], fg_color=COLORS["primary_light"],
                     corner_radius=20, width=285, height=40).pack(side="left", padx=8)
        ctk.CTkLabel(right, text="TERV / DEMÓ", font=("Arial", 14, "bold"),
                     text_color=COLORS["secondary"], fg_color=COLORS["background"],
                     corner_radius=20, width=135, height=40).pack(side="left", padx=8)

        self.top_progress = ctk.CTkFrame(self.header, height=6, fg_color="#E7EFF4", corner_radius=0)
        self.top_progress.place(relx=0, rely=1, anchor="sw", relwidth=1)
        self.top_progress_bar = ctk.CTkFrame(self.top_progress, fg_color=COLORS["primary"], corner_radius=0)
        self.top_progress_bar.place(relx=0, rely=0, relheight=1, relwidth=0.26)

    def create_footer(self):
        self.footer = ctk.CTkFrame(self, height=94, fg_color=COLORS["white"], corner_radius=0,
                                   border_width=1, border_color=COLORS["border"])
        self.footer.grid(row=2, column=0, sticky="ew")
        self.footer.grid_propagate(False)
        self.footer.grid_columnconfigure(2, weight=1)

        outline = dict(fg_color=COLORS["white"], hover_color=COLORS["background"],
                       text_color=COLORS["text"], border_width=1.5,
                       border_color=COLORS["border"], corner_radius=17)

        self.back_button = ctk.CTkButton(self.footer, text="←  Vissza", width=180, height=60,
                                         font=FONTS["normal"], command=self.go_back, **outline)
        self.back_button.grid(row=0, column=0, padx=(65, 10), pady=16)

        self.home_button = ctk.CTkButton(self.footer, text="⌂  Főoldal", width=195, height=60,
                                         font=FONTS["normal"], command=lambda: self.show("MAIN"), **outline)
        self.home_button.grid(row=0, column=1, padx=0, pady=16)

        self.step_label = ctk.CTkLabel(self.footer, text="", font=("Arial", 19, "bold"),
                                       text_color=COLORS["secondary"])
        self.step_label.grid(row=0, column=2, padx=25)

        self.time_label = ctk.CTkLabel(self.footer, text="Eltelt idő  00:00  ·  demonstráció",
                                       font=FONTS["normal"], text_color=COLORS["secondary"])
        self.time_label.grid(row=0, column=3, padx=20)

        self.help_button = ctk.CTkButton(self.footer, text="Segítséget kérek", width=210, height=60,
                                         font=FONTS["normal"], hover_color="#FFF0F1",
                                         fg_color=COLORS["white"], text_color=COLORS["danger"],
                                         border_width=1.5, border_color=COLORS["border"],
                                         corner_radius=17, command=self.show_help)
        self.help_button.grid(row=0, column=4, padx=10, pady=16)

        self.next_button = ctk.CTkButton(self.footer, text="Tovább  →", width=190, height=66,
                                         font=("Arial", 21, "bold"), fg_color=COLORS["primary"],
                                         hover_color=COLORS["primary_hover"],
                                         text_color=COLORS["white"], corner_radius=17,
                                         command=self.next_action)
        self.next_button.grid(row=0, column=5, padx=(10, 65), pady=14)

    def update_footer(self):
        if self.q_data is not None:
            questions = self.q_data["questions"]
            current = self.session["index"]
            self.step_label.configure(text=f"Lépés  {current + 1} / {len(questions)}")
        else:
            self.step_label.configure(text="")

        is_choice = (
            self.q_data is not None
            and self.session["index"] < len(self.q_data["questions"])
            and self.q_data["questions"][self.session["index"]]["type"] == "choice"
        )
        self.next_button.configure(state="normal" if is_choice else "disabled")

    def create_questionnaire_layout(self, frame, node):
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=75, pady=(25, 35))

        has_info = node.get("show_info", False)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1 if has_info else 0)
        for r in range(3):
            content.grid_rowconfigure(r, weight=0)
        content.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(content, text=self.tr(node.get("section", node["title"])).upper(),
                     font=FONTS["section"], text_color=COLORS["primary"]).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        self.q_frame = ctk.CTkFrame(content, fg_color=COLORS["white"], border_width=1.5,
                                    border_color=COLORS["border"], corner_radius=19)
        self.q_frame.grid(row=3, column=0, columnspan=1 if has_info else 2, sticky="nsew")
        self.q_frame.grid_columnconfigure(0, weight=1)
        self.q_frame.grid_rowconfigure(1, weight=1)

        self.question_label = ctk.CTkLabel(content, text="", font=FONTS["heading"],
                                           text_color=COLORS["heading"], anchor="w",
                                           justify="left", wraplength=900)
        self.question_label.grid(row=1, column=0, sticky="w", pady=(0, 5))

        self.subtitle_label = ctk.CTkLabel(
            content,
            text=self.tr(node.get("subtitle", "Kérjük, válaszoljon az alábbi kérdésre.")),
            font=FONTS["subtitle"], text_color=COLORS["secondary"], anchor="w",
        )
        self.subtitle_label.grid(row=2, column=0, sticky="w", pady=(0, 20))

        if has_info:
            self.info_panel = ctk.CTkFrame(content, fg_color=COLORS["primary_light"],
                                           border_width=1.5, border_color="#C8E7E3",
                                           corner_radius=19)
            self.info_panel.grid(row=3, column=1, sticky="nsew", padx=(15, 0))
            self.info_panel.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(self.info_panel,
                         text=self.tr(node.get("info_title", "Mi történik ezután?")),
                         font=("Arial", 29, "bold"), text_color=COLORS["heading"],
                         anchor="w").pack(anchor="w", padx=40, pady=(45, 35))

            ctk.CTkLabel(self.info_panel,
                         text=self.tr(node.get("info_text", "A következő lépésben további információkat kérdezünk.")),
                         font=("Arial", 22), text_color=COLORS["text"], anchor="nw",
                         justify="left", wraplength=400).pack(anchor="w", fill="x", padx=40)

            ctk.CTkLabel(self.info_panel,
                         text=self.tr(node.get("info_badge", "További információ")),
                         font=("Arial", 15, "bold"), text_color=COLORS["primary"],
                         fg_color=COLORS["white"], corner_radius=15,
                         height=40).pack(side="bottom", fill="x", padx=40, pady=55)

        self.btn_frame = ctk.CTkFrame(self.q_frame, fg_color="transparent")
        self.btn_frame.pack(fill="both", expand=True, padx=42, pady=35)