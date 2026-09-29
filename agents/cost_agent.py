from utils.calculations import calculate_option_costs


# Demonstration assumptions only.
# These are not current market prices and must not be presented as
# locally verified agricultural costs.
COST_ASSUMPTIONS = {
    0: {
        "material_unit_cost": 0,
        "material_quantity": 0,
        "labor_cost": 5000,
        "energy_cost": 3000,
        "other_cost": 1000,
    },
    1: {
        "material_unit_cost": 0,
        "material_quantity": 0,
        "labor_cost": 7000,
        "energy_cost": 1000,
        "other_cost": 1500,
    },
    2: {
        "material_unit_cost": 0,
        "material_quantity": 0,
        "labor_cost": 3000,
        "energy_cost": 0,
        "other_cost": 500,
    },
}


def run_cost_agent(farm, interventions):
    """
    Calculate numerical cost estimates for intervention alternatives.

    The values are demonstration assumptions for the hackathon MVP.
    They are not current market prices and should be replaced with
    locally verified prices before real-world use.
    """

    # The application expects exactly three alternatives.
    if not isinstance(interventions, list) or len(interventions) != 3:
        return []

    results = []

    for i, option in enumerate(interventions):
        costs = calculate_option_costs(
            farm,
            i,
            COST_ASSUMPTIONS,
        )

        results.append(
            {
                **option,
                "costs": costs,
                "cost_note": (
                    "Demonstration estimate based on fixed assumptions. "
                    "Not a current local market price."
                ),
            }
        )

    return results
