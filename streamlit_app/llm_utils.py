"""Helper functions for LLM interactions."""
from __future__ import annotations

import os
from typing import List

try:
    from openai import OpenAI
except ImportError:  # fall back to legacy client
    import openai as legacy_openai
    OpenAI = None


def _load_api_key() -> str:
    """Try multiple locations (file or env var) for the API key."""
    try:  # project root
        from app_secrets import OPENAI_API_KEY as key  # type: ignore
        return key
    except ImportError:
        try:  # streamlit_app/app_secrets.py (legacy location)
            from streamlit_app.app_secrets import OPENAI_API_KEY as key  # type: ignore
            return key
        except ImportError:
            return os.getenv("OPENAI_API_KEY", "")


OPENAI_API_KEY = _load_api_key()
MODEL = "gpt-4o-mini"
if OpenAI:
    _client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    _legacy_mode = False
else:
    _client = legacy_openai if OPENAI_API_KEY else None
    _legacy_mode = True
    if _client:
        _client.api_key = OPENAI_API_KEY


def _missing_key_message() -> str:
    return (
        "OpenAI API key missing. Add it to `streamlit_app/app_secrets.py` or set the OPENAI_API_KEY "
        "environment variable."
    )


def summarize_text(text: str) -> str:
    if not text.strip():
        return "Please provide some text to summarize."
    if not _client:
        return _missing_key_message()

    if not _legacy_mode:
        response = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an experienced financial analyst."},
                {"role": "user", "content": f"Summarize the following financial text in under three sentences:\n{text}"},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    else:  # legacy client
        prompt = f"Summarize the following financial text in under three sentences:\n{text}"
        resp = legacy_openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an experienced financial analyst."}, {"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return resp["choices"][0]["message"]["content"].strip()


def chat_with_researcher(history: List[dict], user_input: str) -> str:
    if not user_input.strip():
        return ""
    if not _client:
        return _missing_key_message()

    messages = [
        {
            "role": "system",
            "content": "You are FinResearch Copilot helping analysts interpret news, indices, and risks. Be concise and cite assumptions.",
        },
        *history,
        {"role": "user", "content": user_input},
    ]

    if not _legacy_mode:
        response = _client.chat.completions.create(model=MODEL, messages=messages, temperature=0.5)
        return response.choices[0].message.content.strip()
    else:
        resp = legacy_openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, temperature=0.5)
        return resp["choices"][0]["message"]["content"].strip()
