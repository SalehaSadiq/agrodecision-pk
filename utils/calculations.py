def calculate_intervention_cost(
    material_unit_cost,
    material_quantity,
    labor_cost,
    energy_cost,
    other_cost,
):
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
    return (
        float(probability_of_loss)
        * float(expected_yield_loss)
        * float(crop_value)
    )


def calculate_economic_exposure(
    intervention_cost,
    expected_crop_loss,
):
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
    else:
        water_status = "Unknown"

    if labor_level == "Good":
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
