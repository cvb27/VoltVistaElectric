"""
i18n súper simple (ES/EN) para ir escalando sin reescribir todo.

- Por ahora: usamos un diccionario.
- Más adelante puedes mover esto a archivos JSON por idioma si quieres.
"""

from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "es": {
        "cta_call": "Llamar",
        "cta_text": "Enviar texto",
        "cta_whatsapp": "WhatsApp",

        "hero_title": "Servicios y Reparaciones Eléctricas",
        "hero_subtitle": "Rápido, limpio y orientado a pasar inspección cuando aplique.",
    },
    "en": {
        "cta_call": "Call",
        "cta_text": "Text",
        "cta_whatsapp": "WhatsApp",

        "hero_title": "Electrical Services & Repairs",
        "hero_subtitle": "Fast, clean work with an inspection-ready mindset when applicable.",
    },
}


def t(lang: str, key: str) -> str:
    # Fallback seguro para no romper templates
    lang = (lang or "es").lower()
    if lang not in TRANSLATIONS:
        lang = "es"
    return TRANSLATIONS[lang].get(key, key)
