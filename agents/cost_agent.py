from utils.calculations import calculate_option_costs


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
    Calculate costs for exactly three intervention alternatives.

    These are demonstration estimates and should be replaced with
    locally verified prices before real-world use.
    """

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
                    "Demo estimate — replace with local price "
                    "information before real-world use."
                ),
            }
        )

    return results
