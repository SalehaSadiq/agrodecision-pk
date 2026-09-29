from utils.weather import get_weather
from utils.llm import ask_llm_json


def run_weather_agent(farm):
    """
    Weather & Climate Agent.

    Retrieves public weather data when available and adds a cautious
    interpretation. Weather information is contextual evidence only;
    it does not establish biological causation.
    """

    district = farm.get("district", "Unknown district")
    coords = farm.get("coords")

    weather = get_weather(district, coords)

    fallback_interpretation = (
        "The available weather context may contribute to the reported "
        "crop problem, but weather alone does not establish its cause. "
        "Field verification remains important."
    )

    prompt = f"""
You are the Weather & Climate Agent for AGRODECISION PK.

Given the farm information and weather record below, write one concise
interpretation explaining how the available weather conditions may relate
to the reported crop problem.

Important rules:
- Do not claim that weather caused the problem.
- Do not diagnose the crop.
- Distinguish weather evidence from interpretation.
- Mention uncertainty when appropriate.
- Keep the interpretation practical and concise.
- Return valid JSON with exactly one key: "interpretation".

Farm:
{farm}

Weather:
{weather}
"""

    out = ask_llm_json(
        prompt,
        {"interpretation": fallback_interpretation}
    )

    if isinstance(out, dict):
        interpretation = out.get(
            "interpretation",
            fallback_interpretation
        )
    else:
        interpretation = fallback_interpretation

    weather["interpretation"] = interpretation

    return weather
