"""Helper functions for LLM interactions."""
from __future__ import annotations

from typing import List

import openai

try:
    from secrets import OPENAI_API_KEY
except ImportError:  # pragma: no cover
    OPENAI_API_KEY = ""

openai.api_key = OPENAI_API_KEY
MODEL = "gpt-4o-mini"


def summarize_text(text: str) -> str:
    if not text.strip():
        return "Please provide some text to summarize."
    if not openai.api_key:
        return "OpenAI API key missing (set in secrets.py)."
    prompt = "Summarize the following financial text in under 3 sentences:\n" + text
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "system", "content": "You are an analyst."}, {"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def chat_with_researcher(history: List[dict], user_input: str) -> str:
    if not user_input.strip():
        return ""
    if not openai.api_key:
        return "OpenAI API key missing."
    messages = [
        {
            "role": "system",
            "content": "You are FinResearch Copilot helping analysts interpret news, indices, and risks. Be concise and cite assumptions.",
        }
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})
    resp = openai.ChatCompletion.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content.strip()
