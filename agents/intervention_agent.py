from utils.llm import ask_llm_json


def run_intervention_agent(farm, context, weather, crop_reasoning):
    """
    Intervention Agent.

    Generates exactly three non-ranked intervention alternatives.
    Recommendations remain conditional on field verification and do not
    constitute a confirmed diagnosis or chemical prescription.
    """

    fallback = [
        {
            "name": "Targeted irrigation check and adjustment",
            "what_to_do": (
                "Verify soil/root-zone moisture and, if the field is "
                "genuinely dry, adjust irrigation to the crop's current "
                "need rather than irrigating uniformly without verification."
            ),
            "why_it_may_help": (
                "Addresses the reported water-risk hypothesis while using "
                "verification before spending heavily."
            ),
            "resources": (
                "Water access, basic field inspection, available labor."
            ),
            "timing": "As soon as practical after verification.",
            "potential_benefit": (
                "May reduce water-stress risk if insufficient water is confirmed."
            ),
            "risks": (
                "Unnecessary irrigation can waste water or worsen waterlogging."
            ),
            "uncertainty": (
                "Actual crop water need and soil moisture are unknown."
            ),
        },
        {
            "name": "Field inspection plus localized corrective action",
            "what_to_do": (
                "Inspect representative plants and soil, identify whether "
                "symptoms are uniform or localized, then apply only the "
                "locally justified corrective action."
            ),
            "why_it_may_help": (
                "Separates water, pest, disease and nutrient hypotheses "
                "before committing resources."
            ),
            "resources": (
                "Labor and basic field inspection; local extension support "
                "if available."
            ),
            "timing": "Within 24–48 hours where practical.",
            "potential_benefit": (
                "May reduce the chance of treating the wrong cause."
            ),
            "risks": "Requires time and may delay intervention.",
            "uncertainty": (
                "Cause is not confirmed without field evidence."
            ),
        },
        {
            "name": "Monitor and collect more information",
            "what_to_do": (
                "Record symptom distribution, inspect soil moisture, check "
                "irrigation history and monitor the field before purchasing inputs."
            ),
            "why_it_may_help": (
                "Creates evidence before spending money when the cause is uncertain."
            ),
            "resources": (
                "Farmer/labor time and simple observations."
            ),
            "timing": (
                "Monitor over the next 24–72 hours, depending on crop condition."
            ),
            "potential_benefit": (
                "Can reduce unnecessary expenditure and improve later decisions."
            ),
            "risks": (
                "Delay could be costly if severe stress is already developing."
            ),
            "uncertainty": (
                "Outcome depends on symptom progression and field observations."
            ),
        },
    ]

    prompt = f"""
You are the Intervention Agent for AGRODECISION PK.

Generate exactly 3 practical intervention alternatives for the Pakistani
farm described below.

Return valid JSON containing either:
1. a JSON array of exactly 3 objects, OR
2. an object with one key "options" containing an array of exactly 3 objects.

Each option must contain exactly these required fields:
- name
- what_to_do
- why_it_may_help
- resources
- timing
- potential_benefit
- risks
- uncertainty

Important rules:
- Do NOT rank the options.
- Do NOT identify a "best", "preferred", "optimal", or "recommended"
  option.
- Present them as alternatives for human comparison.
- Do not claim that a biological cause is confirmed.
- Keep actions conditional on appropriate verification.
- Do not prescribe pesticides, fungicides, herbicides, fertilizers, or
  other chemical treatments without adequate evidence.
- If uncertainty is material, include a verification-first or
  monitor-and-learn alternative.
- Consider water availability, labor, farm size and budget.
- Do not invent field observations.
- Keep the alternatives practical for Pakistani farming conditions.

Farm:
{farm}

Farm Context:
{context}

Weather:
{weather}

Crop & Biological Reasoning:
{crop_reasoning}
"""

    out = ask_llm_json(prompt, fallback)

    if isinstance(out, dict) and "options" in out:
        out = out["options"]

    if not isinstance(out, list) or len(out) != 3:
        return fallback

    required_keys = {
        "name",
        "what_to_do",
        "why_it_may_help",
        "resources",
        "timing",
        "potential_benefit",
        "risks",
        "uncertainty",
    }

    for option in out:
        if not isinstance(option, dict):
            return fallback

        if not required_keys.issubset(option.keys()):
            return fallback

    return out
