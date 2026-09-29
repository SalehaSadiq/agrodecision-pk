import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def get_openai_client():

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    if OpenAI is None:
        return None

    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def openai_available():

    return get_openai_client() is not None


def run_openai_prompt(
    prompt,
    model="gpt-5-mini",
):

    client = get_openai_client()

    if client is None:
        return None

    try:

        response = client.responses.create(
            model=model,
            input=prompt,
        )

        return response.output_text

    except Exception:
        return None
