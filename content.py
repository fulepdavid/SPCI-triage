NAME_QUESTION = {
    "type": "text",
    "keyboard_type": "normal",
    "text": {"hu": "Mi a neve?", "en": "Whats your name?"},
    "answer_label": {"hu": "Beteg neve", "en": "Patient's name"},
    "error_label": {"hu": "Adja meg a nevét", "en": "Enter your name"},
    "placeholder": "Adja meg a nevét",
    "required": True,
}

TAJSZAM_QUESTION = {
    "id": "TAJSZAM",
    "type": "text",
    "keyboard_type": "number",
    "text": {"hu": "Adja meg a TAJ számát", "en": "Input your TAJ number"},
    "answer_label": {"hu": "Beteg TAJ száma", "en": "Patient's TAJ number"},
    "error_label": {"hu": "Adja meg a TAJ számát (9 számjegy)", "en": "Enter your TAJ number (9 numbers)"},
    "placeholder": "Adja meg a TAJ számát",
    "required": True,
}

EVSZAM_QUESTION = {
    "type": "text",
    "keyboard_type": "date",
    "text": {"hu": "Adja meg a születési dátumát", "en": "Input your date of birth"},
    "answer_label": {"hu": "Beteg születési dátuma", "en": "Patient's date of birth"},
    "error_label": {"hu": "Adja meg a születési dátumát", "en": "Enter your date of birth"},
    "placeholder": "Adja meg a születési dátumát",
    "required": True,
}

APP = {
    "LANGUAGE": {
        "title": "Select language / Nyelvválasztás",
        "type": "language",
    },

    "MAIN": {
        "title": {"hu": "Vezető panasz", "en": "Leading complaint"},
        "type": "menu",
        "layout": {"cols": 2},
        "hidden_from_search": True,
        "buttons": [
            ({"hu": "Fül-orr-gégészeti", "en": "Ear, nose, and throat"}, "FULORRGEGESZET"),
            ({"hu": "Szemészeti", "en": "Ophthalmology"}, None),
            ({"hu": "Légzési", "en": "Respiratory"}, None),
            ({"hu": "Keringési", "en": "Circulatory"}, None),
            ({"hu": "Sérülés", "en": "Injury"}, None),
            ({"hu": "Idegrendszeri", "en": "Neurological"}, None),
            ({"hu": "Hasi/Emésztési", "en": "Abdominal/Digestive"}, None),
            ({"hu": "Nőgyógyászati", "en": "Gynecological"}, None),
            ({"hu": "Fájdalom/Láz", "en": "Pain/Fever"}, "FAJDALOMLAZ_MENU"),
            ({"hu": "Mellkasi", "en": "Chest"}, None),
            ({"hu": "Vérnyomás mérés", "en": "Blood pressure"}, "BP_MEASURE"),
            ({"hu": "Egyéb", "en": "Other"}, None),
            ({"hu": "Keresés", "en": "Search"}, "KERESES"),
        ],
    },

    "FULORRGEGESZET": {
        "title": {"hu": "Fül-orr-gégészet", "en": "ear, nose, and throat"},
        "type": "menu",
        "buttons": [
            ({"hu": "Orr", "en": "Nose"}, "ORR_MENU"),
            ({"hu": "Fül", "en": "Ear"}, "FUL_MENU"),
            ({"hu": "Torok/Gége", "en": "Throat/Larynx"}, None),
            ({"hu": "Száj", "en": "Mouth"}, None),
            ({"hu": "Nyak", "en": "Neck"}, None),
        ],
        "keywords": {
            "hu": ["fül", "orr", "gége", "teszt"],
            "en": ["ear", "nose", "throat", "test"],
        },
    },

    "ORR_MENU": {
        "title": {"hu": "Orr", "en": "Nose"},
        "type": "menu",
        "buttons": [
            ({"hu": "Orrvérzés", "en": "Nose bleed"}, "ORR_VERZES"),
            ({"hu": "Orrdugulás, szénanátha", "en": "Nasal congestion, hay fever"}, None),
            ({"hu": "Idegentest", "en": "Foreign Body"}, None),
            ({"hu": "Felső légúti fertőzés", "en": "Upper respiratory infection"}, None),
            ({"hu": "Orr sérülés", "en": "Nose injury"}, None),
        ],
    },

    "ORR_VERZES": {
        "type": "questionnaire",
        "title": {"hu": "Orrvérzés", "en": "Nose bleed"},
        "questions": [
            {
                "type": "choice",
                "text": {"hu": "Orrvérzés 1", "en": "Nose bleed 1"},
                "layout": {"cols": 1},
                "options": [
                    {"hu": "Vérzékenység – Intenzíves kezelés korábban", "en": "Bleeding disorder – Previously treated in intensive care"},
                    {"hu": "Vérzékenység – Intenzíves kezelés nem volt", "en": "Bleeding disorder – Not previously treated in intensive care"},
                    {"hu": "Nincs vérzékenység", "en": "No bleeding disorder"},
                ],
            },
            {
                "type": "choice",
                "text": {"hu": "Orrvérzés 2", "en": "Nose bleed 2"},
                "layout": {"cols": 2},
                "options": [
                    {"hu": "Csillapíthatatlan / nyomásra sem csillapodó", "en": "Undamped / not dampened by pressure"},
                    {"hu": "Nyomásra csillapodó", "en": "Dampened by pressure"},
                    {"hu": "Jelenleg nem vérző – első/ritka orrvérzés", "en": "Currently not bleeding – first/rare nosebleed"},
                    {"hu": "Jelenleg nem vérző - Visszatérő orrvérzés", "en": "Currently not bleeding - Recurrent nosebleeds"},
                ],
            },
            NAME_QUESTION,
            TAJSZAM_QUESTION,
            EVSZAM_QUESTION,
        ],
        "end": "LANGUAGE",
    },

    "FUL_MENU": {
        "title": {"hu": "Fül", "en": "Ear"},
        "type": "menu",
        "buttons": [
            ({"hu": "Fülfájás", "en": "Ear pain"}, None),
            ({"hu": "Idegentest a fülben", "en": "Foreign body in ear"}, None),
            ({"hu": "Hallásvesztés/Süketség", "en": "Hearing loss/Deafness"}, "HALLASVESZTES"),
            ({"hu": "Fülzúgás", "en": "Tinnitus"}, "FULZUGAS"),
            ({"hu": "Fülfolyás", "en": "Ear discharge"}, None),
            ({"hu": "Fül sérülés", "en": "Ear injury"}, None),
        ],
    },

    "HALLASVESZTES": {
        "type": "questionnaire",
        "title": {"hu": "Hallásvesztés/Süketség", "en": "Hearing loss/Deafness"},
        "questions": [
            {
                "type": "choice",
                "text": {"hu": "Hallásvesztés/Süketség", "en": "Hearing loss/Deafness"},
                "options": [
                    {"hu": "Hirtelen kezdet", "en": "Sudden onset"},
                    {"hu": "Fokozatos kezdet", "en": "Gradual onset"},
                ],
            },
        ],
        "end": "LANGUAGE",
    },

    "FULZUGAS": {
        "type": "questionnaire",
        "title": {"hu": "Fülzúgás", "en": "Tinnitus"},
        "show_info": True,
        "questions": [
            {
                "type": "choice",
                "text": {"hu": "Fülzúgás", "en": "Tinnitus"},
                "options": [
                    {"hu": "Nagy mennyiségű (4+ tbl/24 óra)Aspirint szedett be az elmúlt 48 órában?", "en": "Have you taken large amounts (4+ tablets/24 hours) of Aspirin in the past 48 hours?"},
                    {"hu": "Nem szedett Aspirint", "en": "Didn't take aspirin"},
                ],
            },
        ],
        "end": "LANGUAGE",
    },

    "FAJDALOMLAZ_MENU": {
        "title": "Fájdalom/Láz",
        "type": "menu",
        "buttons": [
            ({"hu": "Fájdalom, sérülés nem érte", "en": "Pain, no injury."}, None),
            ({"hu": "Fájdalom, sérülés nem érte és légszomj", "en": "Pain, no injury, and shortness of breath"}, None),
            ({"hu": "Fájdalom, sérülés érte", "en": "Pain, suffered injury"}, "FAJDALOM"),
            ({"hu": "Fájdalom és Láz", "en": "Pain and fever"}, "LAZ"),
            ({"hu": "Láz", "en": "Fever"}, None),
        ],
    },

    "FAJDALOM": {
        "type": "questionnaire",
        "title": {"hu": "Fájdalom", "en": "Pain"},
        "questions": [
            {
                "type": "bodymap",
                "text": {"hu": "Hol fáj?", "en": "Where does it hurt?"},
                "images": [
                    {
                        "image": "images/untitled.png",
                        "image_position": [100, 50],
                        "regions": [
                            {"name": "Fej első kép", "rect": [100, 25, 208, 135]},
                            {"name": "Jobb kar", "rect": [27, 180, 86, 390]},
                            {"name": "Jobb kéz", "rect": [26, 391, 77, 462]},
                        ],
                    },
                    {
                        "image": "images/untitled.png",
                        "image_position": [1800, 50],
                        "regions": [
                            {"name": "Fej másik kép", "rect": [100, 25, 208, 135]},
                        ],
                    },
                ],
            },
        ],
        "end": "LANGUAGE",
    },

    "LAZ": {
        "type": "questionnaire",
        "title": {"hu": "Láz", "en": "Fever"},
        "questions": [
            {
                "type": "choice",
                "text": {"hu": "Mióta lázas?", "en": "How long have you had a fever?"},
                "options": [
                    {"hu": "Ma kezdődött", "en": "Started today"},
                    {"hu": "1-3 napja", "en": "1-3 days"},
                    {"hu": "3 napnál régebben", "en": "More than 3 days"},
                ],
            },
            {
                "type": "choice",
                "text": {"hu": "Hidegrázása van?", "en": "Do you have chills?"},
                "options": [
                    {"hu": "Igen", "en": "Yes"},
                    {"hu": "Nem", "en": "No"},
                ],
            },
            {
                "type": "measurement",
                "text": {"hu": "Kérem helyezze a kezét a hőmérőre.", "en": "Please place your hand on the thermometer"},
                "device": "thermometer",
            },
            NAME_QUESTION,
        ],
        "end": "LANGUAGE",
    },

    "BP_MEASURE": {
        "type": "questionnaire",
        "title": {"hu": "Vérnyomásmérés", "en": "Blood pressure"},
        "questions": [
            {
                "type": "choice",
                "text": {
                    "hu": "Helyezze fel a mandzsettát, majd nyomja meg a gombot.",
                    "en": "Put on the cuff, then press the button.",
                },
                "options": [{"hu": "Mérés indítása", "en": "Start measurement"}],
                "answer_label": {"hu": "Mérés indítása", "en": "Start measurement"},
            },
            {
                "type": "measurement",
                "text": {
                    "hu": "Mérés folyamatban, kérjük, maradjon mozdulatlanul.",
                    "en": "Measuring, please keep still.",
                },
                "device": "bp",
                "answer_label": {"hu": "Vérnyomás", "en": "Blood pressure"},
            },
        ],
        "end": "LANGUAGE",
    },

    "KERESES": {
        "title": {"hu": "Keresés", "en": "Search"},
        "type": "search",
        "layout": {"cols": 2},
        "hidden_from_search": True,
    },
}