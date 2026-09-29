
def run_feasibility_agent(farm, options):
    out = []
    for o in options:
        total = o["costs"]["total"]
        if total <= farm["budget"]: budget_status = "Within"
        elif total <= farm["budget"] * 1.25: budget_status = "Near"
        else: budget_status = "Above"
        if farm["water"] == "Limited" and "irrigation" in o["name"].lower(): water_status = "Constrained"
        elif farm["water"] == "Not sure": water_status = "Unknown"
        else: water_status = "Suitable"
        if farm["labor"] == "Low" and ("inspection" in o["name"].lower() or "monitor" in o["name"].lower()): labor_status = "Constrained"
        elif farm["labor"] == "Not sure": labor_status = "Unknown"
        else: labor_status = "Suitable"
        overall = "High" if budget_status == "Within" and water_status != "Constrained" and labor_status != "Constrained" else ("Moderate" if budget_status != "Above" else "Limited")
        out.append({"budget_status": budget_status, "water_status": water_status, "labor_status": labor_status, "overall": overall})
    return out
