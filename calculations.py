def calculate_option_costs(farm, option_index, assumptions):
    key = ["irrigation", "inspection", "monitor"][option_index]
    a = assumptions[key]
    acres = float(farm["farm_size"])
    material = round(acres * a["material_per_acre"])
    labor = round(acres * a["labor_per_acre"])
    energy = round(acres * a["energy_per_acre"])
    equipment = round(acres * a["equipment_per_acre"])
    other = round(acres * a["other_per_acre"])
    total = material + labor + energy + equipment + other
    return {"material": material, "labor": labor, "energy": energy, "equipment": equipment, "other": other, "total": total, "label": "Demonstration estimate"}


def economic_exposure(farm):
    # Transparent demonstration assumptions; intentionally conservative and clearly labelled.
    value_per_acre = {"Wheat": 120000, "Rice": 180000, "Maize": 140000, "Cotton": 170000, "Sugarcane": 220000, "Citrus": 300000, "Mango": 350000}.get(farm["crop"], 150000)
    crop_value = farm["farm_size"] * value_per_acre
    loss_probability = 0.30 if farm["problem"] in ["Water may be insufficient", "Leaves are wilting"] else 0.20
    expected_yield_loss_fraction = 0.15
    expected_loss = crop_value * loss_probability * expected_yield_loss_fraction
    return {"crop_value": round(crop_value), "loss_probability": loss_probability, "yield_loss_fraction": expected_yield_loss_fraction, "expected_loss": round(expected_loss), "label": "Demonstration estimate"}
