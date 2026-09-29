def run_feasibility_agent(farm, options):
    """
    Assess practical feasibility of each intervention alternative.

    This does not rank options or determine which option should be chosen.
    It only compares each option against the farmer's stated budget,
    water availability, and labor availability.
    """

    results = []

    budget = float(farm.get("budget", 0) or 0)
    water = farm.get(
        "water",
        farm.get("water_availability", "Not sure")
    )
    labor = farm.get("labor", "Not sure")

    for option in options:
        costs = option.get("costs", {})
        total = float(costs.get("total", 0) or 0)

        # -------------------------
        # Budget feasibility
        # -------------------------
        if total <= budget:
            budget_status = "Within"
        elif total <= budget * 1.25:
            budget_status = "Near"
        else:
            budget_status = "Above"

        # -------------------------
        # Water feasibility
        # -------------------------
        option_name = str(option.get("name", "")).lower()

        if water == "Limited" and "irrigation" in option_name:
            water_status = "Constrained"
        elif water in {"Not sure", "Unknown"}:
            water_status = "Unknown"
        else:
            water_status = "Suitable"

        # -------------------------
        # Labor feasibility
        # -------------------------
        if labor == "Low" and (
            "inspection" in option_name
            or "monitor" in option_name
        ):
            labor_status = "Constrained"
        elif labor in {"Not sure", "Unknown"}:
            labor_status = "Unknown"
        else:
            labor_status = "Suitable"

        # -------------------------
        # Overall feasibility
        # -------------------------
        if budget_status == "Above":
            overall = "Constrained"
        elif (
            budget_status == "Near"
            or water_status in {"Constrained", "Unknown"}
            or labor_status in {"Constrained", "Unknown"}
        ):
            overall = "Conditionally feasible"
        else:
            overall = "Feasible"

        results.append(
            {
                "budget_status": budget_status,
                "water_status": water_status,
                "labor_status": labor_status,
                "overall": overall,
            }
        )

    return results
