from datetime import datetime, timezone


def build_report(analysis, decision):
    f = analysis["farm"]
    lines = [
        "# AGRODECISION PK — Decision Report", "",
        "## Farm situation", f"- Location: {f['district']}, {f['province']}, Pakistan", f"- Crop: {f['crop']}", f"- Farm size: {f['farm_size']:g} acres", f"- Reported problem: {f['problem']}", f"- Water: {f['water']}", f"- Budget: PKR {f['budget']:,.0f}", f"- Labor: {f['labor']}", "",
        "## AI assessment", analysis["crop_reasoning"]["summary"], "",
        "## Weather", f"- Status: {analysis['weather']['label']}", f"- Temperature: {analysis['weather']['temperature_c']:.1f} °C", f"- Humidity: {analysis['weather']['humidity_pct']:.0f}%", f"- Recent rain: {analysis['weather']['recent_rain_mm']:.1f} mm", analysis["weather"]["interpretation"], "",
        "## Possible causes",
    ]
    for c in analysis["crop_reasoning"]["possible_causes"]:
        lines += [f"- {c['name']} — {c['confidence']}: {c['why']}"]
    lines += ["", "## Intervention alternatives"]
    for i, o in enumerate(analysis["interventions"]):
        lines += [f"### Option {chr(65+i)} — {o['name']}", o["what_to_do"], f"- Estimated cost: PKR {o['costs']['total']:,.0f} ({o['costs']['label']})", f"- Potential benefit: {o['potential_benefit']}", f"- Risks: {o['risks']}", f"- Uncertainty: {o['uncertainty']}"]
    lines += ["", "## AI critic", f"- Key uncertainty: {analysis['critic']['key_uncertainty']}", f"- Alternative explanation: {analysis['critic']['alternative_explanation']}", "- Verify:"]
    lines += [f"  - {x}" for x in analysis["critic"]["verify"]]
    lines += ["", "## Human decision", f"- Decision source: HUMAN USER", f"- Human decision: {decision['action']}", f"- Human modification: {decision.get('human_modification') or 'None'}", f"- Human reasoning: {decision.get('reasoning') or 'Not provided.'}", f"- Timestamp: {decision['timestamp']}", "", "## Assumptions & sources", "- Weather: Open-Meteo public weather API when available; otherwise demo data.", "- Cost figures and economic exposure are demonstration estimates, not official market prices or predictions.", "- District coordinates are approximate lookup values.", "- AI-generated decision support should be verified with qualified local agricultural or extension expertise.", "", "**Final decision made by human user. The AI only provided decision support.**"]
    return "\n".join(lines)
