from utils.calculations import calculate_option_costs
from data.demo_data import COST_ASSUMPTIONS


def run_cost_agent(farm, interventions):
    results = []
    for i, option in enumerate(interventions):
        results.append({**option, "costs": calculate_option_costs(farm, i, COST_ASSUMPTIONS)})
    return results
