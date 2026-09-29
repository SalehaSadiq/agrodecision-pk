def generate_reasoning(
    farm_context,
    weather,
    demo_mode=False,
):

    water_issue = (
        farm_context.get("water_availability") in
        ["Limited", "Moderate", "Not sure"]
    )

    possible_causes = []

    if water_issue:

        possible_causes.append(
            {
                "name": "Possible water stress",
                "explanation": (
                    "Limited or moderate water availability may "
                    "contribute to leaf stress, reduced growth, "
                    "or yellowing depending on crop stage and "
                    "other field conditions."
                ),
                "confidence": "Moderate",
                "supporting_evidence": (
                    "Farmer-reported water availability and "
                    "the reported crop problem."
                ),
                "missing_evidence": (
                    "Actual soil moisture, crop growth stage, "
                    "root condition, and field-wide symptom pattern."
                ),
                "verification": (
                    "Check soil moisture around the root zone "
                    "and compare affected and unaffected plants."
                ),
            }
        )

    possible_causes.append(
        {
            "name": "Possible nutrient-related stress",
            "explanation": (
                "Nutrient imbalance can sometimes produce symptoms "
                "that overlap with water or environmental stress."
            ),
            "confidence": "Low",
            "supporting_evidence": (
                "Visual symptoms may overlap with nutritional stress."
            ),
            "missing_evidence": (
                "Soil testing, fertilizer history, and detailed "
                "symptom distribution."
            ),
            "verification": (
                "Check whether symptoms are uniform across the field "
                "and review recent fertilizer application."
            ),
        }
    )

    possible_causes.append(
        {
            "name": "Possible pest or disease-related stress",
            "explanation": (
                "Some pests and diseases can produce leaf discoloration "
                "or reduced plant vigor that may resemble environmental stress."
            ),
            "confidence": "Low",
            "supporting_evidence": (
                "Crop symptoms alone are not sufficient to exclude "
                "biotic causes."
            ),
            "missing_evidence": (
                "Visible pest presence, lesions, affected plant parts, "
                "and field distribution."
            ),
            "verification": (
                "Inspect both sides of leaves and compare affected "
                "plants with unaffected plants."
            ),
        }
    )

    field_verification = [
        "Examine several affected and unaffected plants.",
        "Check soil moisture around the root zone.",
        "Check whether symptoms occur mainly on old or new leaves.",
        "Inspect leaves for visible insects, lesions, or unusual spots.",
        "Compare symptoms across different parts of the field.",
    ]

    return {
        "possible_causes": possible_causes,
        "field_verification": field_verification,
        "interpretation_note": (
            "These are AI-generated hypotheses for decision support "
            "and are not confirmed diagnoses."
        ),
    }
