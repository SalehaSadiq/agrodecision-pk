from utils.llm import ask_llm_json


def run_crop_agent(farm, context, weather):
    fallback = {
        "summary": "The symptoms are compatible with more than one explanation. The system therefore treats these as hypotheses rather than a diagnosis.",
        "possible_causes": [
            {"name": "Water stress or root-zone limitation", "confidence": "Moderate", "why": "The reported water situation and symptoms can be consistent with inadequate water availability."},
            {"name": "Weather-related stress", "confidence": "Low", "why": "Recent temperature, rainfall and atmospheric conditions can alter crop water demand."},
            {"name": "Pest, disease or nutrient-related stress", "confidence": "Low", "why": "Similar visible symptoms can arise from biological or nutritional causes and need field verification."},
        ],
    }
    prompt = f"""You are the Crop & Biological Reasoning Agent for Pakistani agriculture. Return JSON only with keys summary and possible_causes. possible_causes must contain exactly 3 objects with name, confidence (Low/Moderate/High), why. Do not diagnose or prescribe. Farm={farm}; Context={context}; Weather={weather}"""
    return ask_llm_json(prompt, fallback)
