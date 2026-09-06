"""
Internationalization module for CTFd Account Provisioning plugin.
Supports Vietnamese (vi) and English (en).
"""

from .en import TRANSLATIONS as EN_TRANSLATIONS
from .vi import TRANSLATIONS as VI_TRANSLATIONS

_LANGUAGES = {
    "en": EN_TRANSLATIONS,
    "vi": VI_TRANSLATIONS,
}

DEFAULT_LANGUAGE = "en"


def get_text(key, lang=None):
    """
    Get a translated string by key and language code.

    :param key: Translation key
    :param lang: Language code ('en' or 'vi')
    :return: Translated string, or the key itself if not found
    """
    if lang is None:
        lang = DEFAULT_LANGUAGE
    translations = _LANGUAGES.get(lang, _LANGUAGES[DEFAULT_LANGUAGE])
    return translations.get(key, EN_TRANSLATIONS.get(key, key))


def get_supported_languages():
    """Return list of supported language codes."""
    return list(_LANGUAGES.keys())
