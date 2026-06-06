from __future__ import annotations

import re
from typing import Dict

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Token

LANG_MODELS = {
    "ru": "ru_core_news_sm",
    "en": "en_core_web_sm",
}

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")


class NLPProcessor:
    def __init__(self) -> None:
        self._models: Dict[str, Language] = {}

    def _load_model(self, lang: str) -> Language:
        if lang not in LANG_MODELS:
            raise ValueError(f"Unsupported language: {lang}")
        if lang not in self._models:
            self._models[lang] = spacy.load(LANG_MODELS[lang])
        return self._models[lang]

    def detect_language(self, text: str) -> str:
        if CYRILLIC_RE.search(text):
            return "ru"
        return "en"

    def parse_text(self, text: str, lang: str | None = None) -> Doc:
        if not text.strip():
            raise ValueError("Text must not be empty")
        if lang is None or lang == "auto":
            lang = self.detect_language(text)
        model = self._load_model(lang)
        return model(text)

    @staticmethod
    def get_token_data(token: Token) -> dict:
        return {
            "idx": token.i,
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "morph": token.morph.to_dict(),
            "dep": token.dep_,
            "head": token.head.i,
            "is_root": token.dep_ == "ROOT",
        }

    def extract_tokens(self, doc: Doc) -> list[dict]:
        return [self.get_token_data(token) for token in doc]
