import customtkinter as ctk

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