import json
import os
import requests
import streamlit as st


# =========================================================
# SECRET / ENVIRONMENT HELPERS
# =========================================================

def get_secret(name, default=None):
    """
    Read a setting from Streamlit Secrets first,
    then fall back to an environment variable.
    """

    try:
        if name in st.secrets:
            value = st.secrets[name]

            if value is not None:
                return value

    except Exception:
        pass

    return os.getenv(
        name,
        default,
    )


def has_live_llm():
    """
    Return True when an OpenAI API key is available.
    """

    return bool(
        get_secret(
            "OPENAI_API_KEY"
        )
    )


# =========================================================
# RESPONSE PARSING
# =========================================================

def _responses_text(data):
    """
    Extract text from an OpenAI Responses API response.
    """

    if not isinstance(
        data,
        dict,
    ):
        return ""

    # Preferred Responses API field
    output_text = data.get(
        "output_text"
    )

    if isinstance(
        output_text,
        str,
    ) and output_text.strip():

        return output_text

    # Fallback parser
    chunks = []

    for item in data.get(
        "output",
        [],
    ):

        if not isinstance(
            item,
            dict,
        ):
            continue

        content_items = item.get(
            "content",
            [],
        )

        if not isinstance(
            content_items,
            list,
        ):
            continue

        for content in content_items:

            if not isinstance(
                content,
                dict,
            ):
                continue

            text = content.get(
                "text"
            )

            if isinstance(
                text,
                str,
            ) and text.strip():

                chunks.append(
                    text
                )

    return "\n".join(
        chunks
    )


# =========================================================
# JSON CLEANING
# =========================================================

def _clean_json_text(text):
    """
    Remove common Markdown code fences before JSON parsing.
    """

    text = text.strip()

    if text.startswith(
        "```json"
    ):

        text = text[
            len("```json"):
        ].strip()

    elif text.startswith(
        "```"
    ):

        text = text[
            len("```"):
        ].strip()

    if text.endswith(
        "```"
    ):

        text = text[
            :-3
        ].strip()

    return text


# =========================================================
# OPENAI JSON REQUEST
# =========================================================

def ask_llm_json(
    prompt,
    fallback,
):
    """
    Ask the OpenAI Responses API for JSON.

    If no API key is configured, or if the API request fails,
    return the supplied deterministic fallback.
    """

    key = get_secret(
        "OPENAI_API_KEY"
    )

    # -----------------------------------------------------
    # DEMO / FALLBACK MODE
    # -----------------------------------------------------

    if not key:

        return fallback

    model = get_secret(
        "OPENAI_MODEL",
        "gpt-5.6-luna",
    )

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "input": prompt,
    }

    try:

        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        text = _responses_text(
            data
        ).strip()

        if not text:

            return fallback

        text = _clean_json_text(
            text
        )

        result = json.loads(
            text
        )

        return result

    except Exception:

        # -------------------------------------------------
        # IMPORTANT:
        # The application should remain functional even
        # when the external AI service is unavailable.
        # -------------------------------------------------

        return fallback
