from utils.calculations import calculate_option_costs
from utils.calculations import economic_exposure


def run_cost_agent(farm, interventions):
    results = []
    for i, option in enumerate(interventions):
        results.append({**option, "costs": calculate_option_costs(farm, i, COST_ASSUMPTIONS)})
    return results
