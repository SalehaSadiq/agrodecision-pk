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
    Expected Crop Loss =
    Probability of loss × Expected yield loss × Crop value

    This is an estimate for decision support, not a prediction.
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
    Economic Exposure =
    Intervention Cost − Expected Crop Loss

    This is an AI-generated decision-support estimate.
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
    Calculate feasibility without ranking interventions.
    """

    budget = float(budget)
    total_cost = float(total_cost)

    if total_cost <= budget:
        budget_status = "Within"
    elif total_cost <= budget * 1.25:
        budget_status = "Near"
    else:
        budget_status = "Above"

    if water_availability == "Good":
        water_status = "Suitable"
    elif water_availability == "Limited":
        water_status = "Constrained"
    elif water_availability == "Moderate":
        water_status = "Suitable"
    else:
        water_status = "Unknown"

    if labor_level in ("Good", "Moderate"):
        labor_status = "Suitable"
    elif labor_level == "Limited":
        labor_status = "Constrained"
    else:
        labor_status = "Unknown"

    constraints = 0

    if budget_status == "Above":
        constraints += 1

    if water_status == "Constrained":
        constraints += 1

    if labor_status == "Constrained":
        constraints += 1

    if constraints == 0:
        overall = "High"
    elif constraints == 1:
        overall = "Moderate"
    else:
        overall = "Limited"

    return {
        "budget": budget_status,
        "water": water_status,
        "labor": labor_status,
        "overall": overall,
    }


def calculate_option_costs(farm, option_index, cost_assumptions):
    """
    Calculate the cost of one intervention option.

    All calculations are performed in Python.
    The supplied assumptions are demonstration assumptions unless
    replaced by locally verified prices.
    """

    assumptions = cost_assumptions.get(
        option_index,
        cost_assumptions.get(str(option_index), {}),
    )

    return calculate_intervention_cost(
        material_unit_cost=assumptions.get("material_unit_cost", 0),
        material_quantity=assumptions.get("material_quantity", 0),
        labor_cost=assumptions.get("labor_cost", 0),
        energy_cost=assumptions.get("energy_cost", 0),
        other_cost=assumptions.get("other_cost", 0),
    )


def economic_exposure_from_farm(
    farm,
    intervention_cost=0,
    probability_of_loss=0.0,
    expected_yield_loss=0.0,
    crop_value=0.0,
):
    """
    Convenience function for agents that need an economic estimate.

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
