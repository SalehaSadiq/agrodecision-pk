import json
import os
import requests
import streamlit as st


def get_secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def has_live_llm():
    return bool(get_secret("OPENAI_API_KEY"))


def _responses_text(data):
    if isinstance(data.get("output_text"), str) and data["output_text"].strip():
        return data["output_text"]
    chunks = []
    for item in data.get("output", []):
        for content in item.get("content", []) if isinstance(item, dict) else []:
            if isinstance(content, dict) and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks)


def ask_llm_json(prompt, fallback):
    key = get_secret("OPENAI_API_KEY")
    if not key:
        return fallback
    model = get_secret("OPENAI_MODEL", "gpt-5.6-luna")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        payload = {"model": model, "input": prompt, "temperature": 0.2}
        r = requests.post("https://api.openai.com/v1/responses", headers=headers, json=payload, timeout=25)
        r.raise_for_status()
        text = _responses_text(r.json()).strip()
        if text.startswith("```"):
            text = text.replace("```json", "", 1).replace("```", "").strip()
        return json.loads(text)
    except Exception:
        return fallback
