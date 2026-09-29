def calculate_intervention_cost(
    material_unit_cost,
    material_quantity,
    labor_cost,
    energy_cost,
    other_cost,
):
    """
    Calculate intervention cost components using Python.

    All monetary values are in PKR.

    These calculations are deterministic. The quality of the estimate
    depends on the supplied cost assumptions.
    """

    material = float(material_unit_cost) * float(material_quantity)
    labor = float(labor_cost)
    energy = float(energy_cost)
    other = float(other_cost)

    total = material + labor + energy + other

    return {
        "material": material,
        "labor": labor,
        "energy": energy,
        "other": other,
        "total": total,
    }


def calculate_expected_crop_loss(
    probability_of_loss,
    expected_yield_loss,
    crop_value,
):
    """
    Estimate expected crop loss.

    Formula:
        Probability of loss
        × Expected yield loss
        × Crop value

    This is a decision-support estimate, not a prediction.

    The function should only be used when the required values have
    actually been collected or explicitly supplied as assumptions.
    """

    return (
        float(probability_of_loss)
        * float(expected_yield_loss)
        * float(crop_value)
    )


def calculate_economic_exposure(
    intervention_cost,
    expected_crop_loss,
):
    """
    Calculate a simple net economic comparison:

        Intervention cost − expected crop loss

    This function is retained for future decision-support scenarios,
    but the result should not be presented as a standard financial
    measure or prediction.

    Do not use this calculation with invented crop-loss assumptions.
    """

    return (
        float(intervention_cost)
        - float(expected_crop_loss)
    )


def calculate_feasibility(
    budget,
    total_cost,
    water_availability,
    labor_level="Moderate",
):
    """
    Assess practical feasibility without ranking interventions.

    Returns descriptive statuses rather than a numerical or ordinal
    recommendation score.
    """

    budget = float(budget)
    total_cost = float(total_cost)

    # Budget
    if total_cost <= budget:
        budget_status = "Within"
    elif total_cost <= budget * 1.25:
        budget_status = "Near"
    else:
        budget_status = "Above"

    # Water
    if water_availability == "Good":
        water_status = "Suitable"
    elif water_availability == "Moderate":
        water_status = "Suitable"
    elif water_availability == "Limited":
        water_status = "Constrained"
    else:
        water_status = "Unknown"

    # Labor
    if labor_level in ("Good", "Moderate"):
        labor_status = "Suitable"
    elif labor_level in ("Low", "Limited"):
        labor_status = "Constrained"
    else:
        labor_status = "Unknown"

    # Overall feasibility is descriptive, not a ranking.
    if (
        budget_status == "Above"
        or water_status == "Constrained"
        or labor_status == "Constrained"
    ):
        overall = "Constrained"
    elif (
        budget_status == "Near"
        or water_status == "Unknown"
        or labor_status == "Unknown"
    ):
        overall = "Conditionally feasible"
    else:
        overall = "Feasible"

    return {
        "budget": budget_status,
        "water": water_status,
        "labor": labor_status,
        "overall": overall,
    }


def calculate_option_costs(
    farm,
    option_index,
    cost_assumptions,
):
    """
    Calculate the cost of one intervention option.

    All calculations are performed deterministically in Python.

    The supplied assumptions are demonstration assumptions unless
    replaced with locally verified prices.

    The farm argument is retained so that the function can later
    incorporate farm-size-dependent calculations without changing
    the agent interface.
    """

    assumptions = cost_assumptions.get(
        option_index,
        cost_assumptions.get(str(option_index), {}),
    )

    return calculate_intervention_cost(
        material_unit_cost=assumptions.get(
            "material_unit_cost",
            0,
        ),
        material_quantity=assumptions.get(
            "material_quantity",
            0,
        ),
        labor_cost=assumptions.get(
            "labor_cost",
            0,
        ),
        energy_cost=assumptions.get(
            "energy_cost",
            0,
        ),
        other_cost=assumptions.get(
            "other_cost",
            0,
        ),
    )


def economic_exposure_from_farm(
    farm,
    intervention_cost=0,
    probability_of_loss=0.0,
    expected_yield_loss=0.0,
    crop_value=0.0,
):
    """
    Convenience function for future economic analysis.

    Expected crop loss and economic exposure are only meaningful when
    the underlying assumptions are explicitly supplied.

    The result is an estimate for decision support, not a prediction.
    """

    expected_loss = calculate_expected_crop_loss(
        probability_of_loss,
        expected_yield_loss,
        crop_value,
    )

    exposure = calculate_economic_exposure(
        intervention_cost,
        expected_loss,
    )

    return {
        "expected_crop_loss": expected_loss,
        "economic_exposure": exposure,
    }
