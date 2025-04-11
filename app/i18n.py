import json
from pathlib import Path

TRANSLATIONS = {}

def load_translations():
    folder = Path(__file__).parent / "translations"
    for file in folder.glob("*.json"):
        lang = file.stem
        with open(file, "r", encoding="utf-8") as f:
            TRANSLATIONS[lang] = json.load(f)

def get_translations(lang: str = "pt"):
    return TRANSLATIONS.get(lang, TRANSLATIONS["pt"])
