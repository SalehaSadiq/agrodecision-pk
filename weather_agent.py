from utils.weather import get_weather
from utils.llm import ask_llm_json


def run_weather_agent(farm):
    weather = get_weather(farm["district"], farm["coords"])
    fallback_interpretation = "The available weather context may contribute to the reported crop problem, but weather alone does not establish its cause. Field verification remains important."
    prompt = f"""You are the Weather & Climate Agent. Given this farm and weather record, write one concise interpretation explaining how the conditions may relate to the reported problem. Never claim weather proves causation. Return JSON with key interpretation. Farm={farm}; Weather={weather}"""
    out = ask_llm_json(prompt, {"interpretation": fallback_interpretation})
    weather["interpretation"] = out.get("interpretation", fallback_interpretation)
    return weather
