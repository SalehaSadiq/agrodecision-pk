from utils.llm import ask_llm_json
from utils.calculations import economic_exposure


def run_critic_agent(farm, context, weather, crop_reasoning, options, feasibility):
    exposure = economic_exposure(farm)
    fallback = {
        "key_uncertainty": "The reported symptoms have not been verified through a field inspection, and crop stage, soil moisture and irrigation history are incomplete.",
        "missing_information": ["Crop growth stage", "Soil/root-zone moisture", "Irrigation history", "Pattern of symptoms across the field"],
        "alternative_explanation": "Pest, disease or nutrient-related stress could produce overlapping visible symptoms.",
        "verify": ["Inspect representative plants and roots", "Check soil/root-zone moisture", "Review recent irrigation and rainfall", "Seek local extension or crop-specialist input if symptoms persist or worsen"],
        "confidence": "Moderate",
        "economic_exposure": exposure,
    }
    prompt = f"""You are a skeptical AI Critic. Challenge the analysis without selecting an option. Return JSON with key_uncertainty, missing_information array, alternative_explanation, verify array, confidence, economic_exposure. Farm={farm}; Context={context}; Weather={weather}; Crop={crop_reasoning}; Options={options}; Feasibility={feasibility}"""
    out = ask_llm_json(prompt, fallback)
    if not isinstance(out, dict): return fallback
    out["economic_exposure"] = exposure
    return out
