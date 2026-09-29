def generate_interventions(
    farm_context,
    reasoning,
    budget,
    demo_mode=False,
):

    return [
        {
            "name": "Targeted irrigation adjustment",
            "what_to_do": (
                "Review root-zone moisture and, if the field is "
                "confirmed to be dry, provide an appropriate irrigation "
                "event rather than irrigating solely on symptoms."
            ),
            "why_it_may_help": (
                "If water stress is contributing to the symptoms, "
                "restoring adequate soil moisture may reduce stress."
            ),
            "timing": "After field moisture verification.",
            "resources": "Water, irrigation access, labor.",
            "benefit": "May reduce water-stress symptoms if water shortage is confirmed.",
            "risks": "Unnecessary irrigation could waste water or increase waterlogging risk.",
            "uncertainty": "Moderate because the cause has not been confirmed.",
            "cost_inputs": {
                "material_unit_cost": 0,
                "material_quantity": 1,
                "labor_cost": 4000,
                "energy_cost": 2500,
                "other_cost": 500,
            },
            "economic_inputs": {
                "probability_of_loss": 0.30,
                "expected_yield_loss": 0.15,
                "crop_value": 100000,
            },
        },
        {
            "name": "Field monitoring and targeted management",
            "what_to_do": (
                "Monitor affected and unaffected plants for several days "
                "while checking soil moisture, symptom progression, "
                "and visible pest or disease evidence."
            ),
            "why_it_may_help": (
                "Additional observations can help distinguish between "
                "water, nutrient, and biotic explanations before spending."
            ),
            "timing": "Monitor over the next 3–5 days.",
            "resources": "Labor and field observation.",
            "benefit": "May improve diagnostic confidence before intervention.",
            "risks": "Delay could be undesirable if the underlying problem is severe.",
            "uncertainty": "Moderate to high.",
            "cost_inputs": {
                "material_unit_cost": 500,
                "material_quantity": 1,
                "labor_cost": 2500,
                "energy_cost": 0,
                "other_cost": 500,
            },
            "economic_inputs": {
                "probability_of_loss": 0.35,
                "expected_yield_loss": 0.20,
                "crop_value": 100000,
            },
        },
        {
            "name": "Verification-first low-cost approach",
            "what_to_do": (
                "Avoid immediate major spending. First verify soil moisture, "
                "symptom distribution, recent management history, and "
                "visible pest or disease indicators."
            ),
            "why_it_may_help": (
                "It reduces the chance of applying an unnecessary intervention "
                "when the cause remains uncertain."
            ),
            "timing": "Immediately, before major intervention.",
            "resources": "Farmer observation and basic field labor.",
            "benefit": "May reduce unnecessary expenditure under uncertainty.",
            "risks": "Waiting may allow a genuine problem to progress.",
            "uncertainty": "High until more evidence is collected.",
            "cost_inputs": {
                "material_unit_cost": 0,
                "material_quantity": 1,
                "labor_cost": 1500,
                "energy_cost": 0,
                "other_cost": 250,
            },
            "economic_inputs": {
                "probability_of_loss": 0.40,
                "expected_yield_loss": 0.25,
                "crop_value": 100000,
            },
        },
    ]
