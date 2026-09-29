from utils.llm import ask_llm_json


def run_critic_agent(
    farm,
    context,
    weather,
    crop_reasoning,
    options,
    feasibility,
):
    """
    Critic Agent.

    Challenges assumptions, identifies missing information, and suggests
    field verification steps.

    It does not diagnose the crop and does not select, rank, or score
    intervention alternatives.
    """

    # Calculate the combined displayed cost of the alternatives.
    # This is NOT an expected farmer expenditure because the alternatives
    # are mutually alternative choices.
    alternative_costs = []

    for option in options:
        try:
            total = float(
                option.get("costs", {}).get("total", 0) or 0
            )
        except (TypeError, ValueError):
            total = 0.0

        alternative_costs.append(total)

    fallback = {
        "key_uncertainty": (
            "The reported symptoms have not been verified through field "
            "inspection, and crop stage, soil moisture and recent irrigation "
            "history remain incomplete."
        ),
        "missing_information": [
            "Crop growth stage",
            "Soil/root-zone moisture",
            "Irrigation history",
            "Pattern of symptoms across the field",
        ],
        "alternative_explanation": (
            "Pest, disease or nutrient-related stress could produce "
            "overlapping visible symptoms."
        ),
        "verify": [
            "Inspect representative plants and roots",
            "Check soil/root-zone moisture",
            "Review recent irrigation and rainfall",
            "Seek local extension or crop-specialist input if symptoms "
            "persist or worsen",
        ],
        "confidence": "Moderate",
        "alternative_costs": alternative_costs,
        "economic_note": (
            "The displayed intervention costs are alternative estimates, "
            "not a prediction of crop loss or total farmer expenditure."
        ),
    }

    prompt = f"""
You are a skeptical AI Critic for AGRODECISION PK, a Pakistani
agriculture decision-support prototype.

Your task is to challenge the analysis before the human makes a decision.

Return valid JSON only with these keys:
- key_uncertainty
- missing_information
- alternative_explanation
- verify
- confidence

Rules:
- missing_information must be an array.
- verify must be an array.
- confidence must be one of: Low, Moderate, High.
- Do not diagnose the crop.
- Do not claim certainty.
- Do not rank interventions.
- Do not select a preferred intervention.
- Identify important missing evidence.
- Consider whether the weather evidence is sufficient.
- Consider whether the biological hypotheses have enough field evidence.
- Consider uncertainty in the cost estimates.
- Identify potential unintended consequences where relevant.
- Suggest practical field checks.
- Do not invent observations, prices, crop losses, yields, probabilities,
  or economic values.

Farm:
{farm}

Context:
{context}

Weather:
{weather}

Crop reasoning:
{crop_reasoning}

Options:
{options}

Feasibility:
{feasibility}
"""

    out = ask_llm_json(prompt, fallback)

    if not isinstance(out, dict):
        return fallback

    required_keys = {
        "key_uncertainty",
        "missing_information",
        "alternative_explanation",
        "verify",
        "confidence",
    }

    if not required_keys.issubset(out.keys()):
        return fallback

    if not isinstance(out.get("missing_information"), list):
        return fallback

    if not isinstance(out.get("verify"), list):
        return fallback

    if out.get("confidence") not in {"Low", "Moderate", "High"}:
        return fallback

    # Keep the numerical cost information deterministic and separate from
    # the LLM's qualitative critique.
    out["alternative_costs"] = alternative_costs

    out["economic_note"] = (
        "The displayed intervention costs are alternative estimates, "
        "not a prediction of crop loss or total farmer expenditure."
    )

    return out
