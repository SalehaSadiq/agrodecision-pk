def calculate_material_cost(unit_cost, quantity):
    return float(unit_cost) * float(quantity)


def calculate_total_cost(
    material_cost,
    labor_cost,
    energy_cost,
    other_cost,
):
    return (
        float(material_cost)
        + float(labor_cost)
        + float(energy_cost)
        + float(other_cost)
    )


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
    return float(intervention_cost) - float(expected_crop_loss)
