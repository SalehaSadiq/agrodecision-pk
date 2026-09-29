def generate_critic(
    farm_context,
    reasoning,
    interventions,
    weather,
):

    return {
        "key_uncertainty": (
            "The reported symptoms do not uniquely identify their cause."
        ),
        "missing_information": (
            "Soil moisture, crop growth stage, symptom distribution, "
            "and detailed pest/disease observations are incomplete."
        ),
        "alternative_explanation": (
            "Nutrient stress or pest/disease pressure could overlap "
            "with symptoms associated with water stress."
        ),
        "verification": (
            "Inspect multiple plants and compare affected and unaffected "
            "areas before committing substantial resources."
        ),
        "confidence": "Moderate",
    }
