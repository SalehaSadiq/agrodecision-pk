from utils.llm import ask_llm_json


def run_context_agent(farm):
    fallback = {
        "summary": f"A {farm['farm_size']:g}-acre {farm['crop']} farm in {farm['district']}, {farm['province']} is reporting: {farm['problem']}. Water is {farm['water'].lower()} and the stated budget is PKR {farm['budget']:,.0f}.",
        "important_factors": [f"Reported issue: {farm['problem']}", f"Water availability: {farm['water']}", f"Available budget: PKR {farm['budget']:,.0f}", f"Labor availability: {farm['labor']}", "Crop stage and field-level measurements were not provided."],
        "missing_information": ["Crop growth stage", "Recent irrigation timing and amount", "Field inspection of symptoms", "Soil moisture or root-zone condition"],
    }
    prompt = f"""You are the Farm Context Agent for a Pakistani agriculture decision-support prototype. Return JSON only with keys summary, important_factors (array), missing_information (array). Do not diagnose. Farm: {farm}"""
    return ask_llm_json(prompt, fallback)
