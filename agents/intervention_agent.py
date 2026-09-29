from utils.llm import ask_llm_json


def run_crop_agent(farm, context, weather):
    """
    Crop & Biological Reasoning Agent.

    Produces three possible explanations as hypotheses, not a diagnosis.
    The output is intentionally structured so that the human user can
    compare alternatives and verify them in the field.
    """

    fallback = {
        "summary": (
            "The reported symptoms are compatible with more than one "
            "explanation. The system therefore treats these as hypotheses "
            "rather than a diagnosis."
        ),
        "possible_causes": [
            {
                "name": "Water stress or root-zone limitation",
                "confidence": "Moderate",
                "why": (
                    "The reported water situation and symptoms can be "
                    "consistent with inadequate water availability."
                ),
            },
            {
                "name": "Weather-related stress",
                "confidence": "Low",
                "why": (
                    "Recent temperature, rainfall and atmospheric "
                    "conditions can alter crop water demand."
                ),
            },
            {
                "name": "Pest, disease or nutrient-related stress",
                "confidence": "Low",
                "why": (
                    "Similar visible symptoms can arise from biological "
                    "or nutritional causes and require field verification."
                ),
            },
        ],
    }

    prompt = f"""
You are the Crop & Biological Reasoning Agent for AGRODECISION PK,
a human-in-the-loop agricultural decision-support system for Pakistan.

Analyze the farm information, farm context, and available weather evidence.

Return valid JSON only with exactly these keys:
- "summary"
- "possible_causes"

"possible_causes" must contain exactly 3 objects.

Each object must contain:
- "name"
- "confidence"
- "why"

The confidence value must be exactly one of:
- "Low"
- "Moderate"
- "High"

Important rules:
- These are hypotheses, NOT diagnoses.
- Do not claim that any cause is confirmed.
- Do not prescribe a treatment here.
- Use the available farmer-provided information and weather evidence.
- Do not invent observations that were not provided.
- Clearly reflect uncertainty.
- Consider alternative explanations where appropriate.
- Keep the reasoning practical for a farmer or agricultural advisor.
- The three possibilities must be meaningfully different rather than three
  versions of the same explanation.

Farm:
{farm}

Farm Context:
{context}

Weather:
{weather}
"""

    result = ask_llm_json(prompt, fallback)

    # Defensive validation for hackathon reliability.
    if not isinstance(result, dict):
        return fallback

    causes = result.get("possible_causes")

    if not isinstance(causes, list) or len(causes) != 3:
        return fallback

    required_keys = {"name", "confidence", "why"}
    valid_confidence = {"Low", "Moderate", "High"}

    for cause in causes:
        if not isinstance(cause, dict):
            return fallback

        if not required_keys.issubset(cause.keys()):
            return fallback

        if cause.get("confidence") not in valid_confidence:
            return fallback

    if not isinstance(result.get("summary"), str):
        return fallback

    return result
