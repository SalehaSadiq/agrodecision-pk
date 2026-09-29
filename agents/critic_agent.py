from utils.llm import ask_llm_json
from utils.calculations import calculate_economic_exposure


def run_critic_agent(
    farm,
    context,
    weather,
    crop_reasoning,
    options,
    feasibility,
):
    """
    Critic agent challenges assumptions and uncertainty.
    It does not select an intervention.
    """

    total_intervention_cost = sum(
        float(
            option.get("costs", {}).get("total", 0)
        )
        for option in options
    )

    # No crop-loss probability/value is assumed here unless
    # the application has actually collected those values.
    # Therefore the default expected crop loss is zero.
    expected_crop_loss = 0.0

    exposure = calculate_economic_exposure(
        total_intervention_cost,
        expected_crop_loss,
    )

    fallback = {
        "key_uncertainty": (
            "The reported symptoms have not been verified through "
            "field inspection, and crop stage, soil moisture and "
            "irrigation history remain incomplete."
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
        "economic_exposure": exposure,
    }

    prompt = f"""
You are a skeptical AI Critic for a Pakistani agriculture
decision-support prototype.

Challenge the analysis without selecting or ranking an option.

Return JSON only with these keys:
key_uncertainty
missing_information
alternative_explanation
verify
confidence

missing_information and verify must be arrays.

Do not diagnose.
Do not claim certainty.
Do not rank interventions.

Farm={farm}

Context={context}

Weather={weather}

Crop reasoning={crop_reasoning}

Options={options}

Feasibility={feasibility}
"""

    out = ask_llm_json(prompt, fallback)

    if not isinstance(out, dict):
        return fallback

    out["economic_exposure"] = exposure

    return out
