import json
from pathlib import Path

from utils.llm import ask_llm_json


EVIDENCE_FILE = Path("data/evidence_sources.json")


def _load_evidence():
    """
    Load verified agricultural evidence from the local evidence database.
    """

    if not EVIDENCE_FILE.exists():
        return []

    try:
        with open(EVIDENCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        return data

    except (json.JSONDecodeError, OSError):
        return []


def _extract_crop(farm):
    """
    Identify the crop from the farm information.
    """

    if not isinstance(farm, dict):
        return ""

    possible_keys = [
        "crop",
        "crop_name",
        "crop type",
        "crop_type",
        "Crop",
        "Crop Name",
    ]

    for key in possible_keys:
        value = farm.get(key)

        if value:
            return str(value).strip()

    return ""


def _get_relevant_evidence(farm):
    """
    Select verified evidence relevant to the reported crop.

    Crop-specific evidence and general evidence are included.
    """

    evidence = _load_evidence()

    if not evidence:
        return []

    crop = _extract_crop(farm).lower()

    relevant = []

    for item in evidence:
        if not isinstance(item, dict):
            continue

        evidence_crop = str(
            item.get("crop", "")
        ).strip().lower()

        if not evidence_crop:
            continue

        if evidence_crop == "general":
            relevant.append(item)

        elif crop and evidence_crop == crop:
            relevant.append(item)

    return relevant


def _format_evidence_for_prompt(evidence):
    """
    Convert verified evidence into a readable format for the LLM.

    The model receives the actual evidence record and its ID.
    """

    if not evidence:
        return "No verified external research evidence is currently available."

    formatted = []

    for item in evidence:
        evidence_id = item.get("id", "UNKNOWN")
        source_type = item.get("source_type", "")
        title = item.get("title", "Untitled source")
        authors = item.get("authors", "")
        year = item.get("year", "")
        journal = item.get("journal", "")
        claim = item.get("claim", "")
        evidence_strength = item.get(
            "evidence_strength",
            ""
        )

        formatted.append(
            f"""
Evidence ID: {evidence_id}
Source type: {source_type}
Citation: {authors} ({year})
Title: {title}
Journal: {journal}
Supported claim: {claim}
Evidence strength: {evidence_strength}
""".strip()
        )

    return "\n\n".join(formatted)


def _build_fallback():
    """
    Safe fallback alternatives used when the LLM response is invalid.
    """

    return [
        {
            "name": "Targeted irrigation check and adjustment",
            "what_to_do": (
                "Verify soil/root-zone moisture and, if the field is "
                "genuinely dry, adjust irrigation to the crop's current "
                "need rather than irrigating uniformly without verification."
            ),
            "why_it_may_help": (
                "Addresses the reported water-risk hypothesis while using "
                "verification before spending heavily."
            ),
            "resources": (
                "Water access, basic field inspection, available labor."
            ),
            "timing": "As soon as practical after verification.",
            "potential_benefit": (
                "May reduce water-stress risk if insufficient water is confirmed."
            ),
            "risks": (
                "Unnecessary irrigation can waste water or worsen waterlogging."
            ),
            "uncertainty": (
                "Actual crop water need and soil moisture are unknown."
            ),
            "evidence_ids": [],
        },
        {
            "name": "Field inspection plus localized corrective action",
            "what_to_do": (
                "Inspect representative plants and soil, identify whether "
                "symptoms are uniform or localized, then apply only the "
                "locally justified corrective action."
            ),
            "why_it_may_help": (
                "Separates water, pest, disease and nutrient hypotheses "
                "before committing resources."
            ),
            "resources": (
                "Labor and basic field inspection; local extension support "
                "if available."
            ),
            "timing": "Within 24–48 hours where practical.",
            "potential_benefit": (
                "May reduce the chance of treating the wrong cause."
            ),
            "risks": (
                "Requires time and may delay intervention."
            ),
            "uncertainty": (
                "Cause is not confirmed without field evidence."
            ),
            "evidence_ids": [],
        },
        {
            "name": "Monitor and collect more information",
            "what_to_do": (
                "Record symptom distribution, inspect soil moisture, check "
                "irrigation history and monitor the field before purchasing inputs."
            ),
            "why_it_may_help": (
                "Creates evidence before spending money when the cause is uncertain."
            ),
            "resources": (
                "Farmer/labor time and simple observations."
            ),
            "timing": (
                "Monitor over the next 24–72 hours, depending on crop condition."
            ),
            "potential_benefit": (
                "Can reduce unnecessary expenditure and improve later decisions."
            ),
            "risks": (
                "Delay could be costly if severe stress is already developing."
            ),
            "uncertainty": (
                "Outcome depends on symptom progression and field observations."
            ),
            "evidence_ids": [],
        },
    ]


def run_intervention_agent(
    farm,
    context,
    weather,
    crop_reasoning,
):
    """
    Intervention Agent.

    Generates exactly three non-ranked intervention alternatives.

    Evidence is supplied from the verified evidence database.
    The model may only reference evidence IDs that actually exist
    in that database.

    Recommendations remain conditional on field verification and
    do not constitute a confirmed diagnosis or chemical prescription.
    """

    fallback = _build_fallback()

    evidence = _get_relevant_evidence(farm)
    evidence_text = _format_evidence_for_prompt(evidence)

    prompt = f"""
You are the Intervention Agent for AGRODECISION PK.

Generate exactly 3 practical intervention alternatives for the Pakistani
farm described below.

Return valid JSON containing either:

1. a JSON array of exactly 3 objects

OR

2. an object with one key "options" containing an array of exactly
   3 objects.

Each option must contain exactly these fields:

- name
- what_to_do
- why_it_may_help
- resources
- timing
- potential_benefit
- risks
- uncertainty
- evidence_ids

"evidence_ids" must be a list.

The list may be empty if no supplied evidence directly supports
the option.

Only use Evidence IDs that appear in the VERIFIED EVIDENCE section.

IMPORTANT RULES:

1. Do NOT rank the options.

2. Do NOT identify a "best", "preferred", "optimal", or "recommended"
   option.

3. Present all three as alternatives for human comparison.

4. Do not claim that a biological cause is confirmed.

5. Keep actions conditional on appropriate field verification.

6. Do not invent scientific studies or citations.

7. Do not invent authors, journals, years, DOI numbers, URLs,
   treatment-effect statistics, application rates, or research findings.

8. You may ONLY use research evidence supplied in the VERIFIED
   EVIDENCE section.

9. If the evidence does not support an intervention, use:
   "evidence_ids": []

10. Do not make a stronger claim than the supplied evidence supports.

11. Research evidence from another location, crop variety, season,
    or farming system does not guarantee the same outcome on this farm.

12. Do not prescribe pesticides, fungicides, herbicides, fertilizers,
    or other chemical treatments without adequate evidence and
    appropriate verification.

13. If uncertainty is material, include a verification-first or
    monitor-and-learn alternative.

14. Consider water availability, labor, farm size and budget.

15. Do not invent field observations.

16. Keep alternatives practical for Pakistani farming conditions.

17. The human user remains responsible for the final farm decision.

FARM:
{farm}

FARM CONTEXT:
{context}

WEATHER:
{weather}

CROP & BIOLOGICAL REASONING:
{crop_reasoning}

VERIFIED EVIDENCE:
{evidence_text}
"""

    out = ask_llm_json(prompt, fallback)

    # ---------------------------------------------------------
    # Normalize possible {"options": [...]} response
    # ---------------------------------------------------------

    if isinstance(out, dict) and "options" in out:
        out = out["options"]

    # ---------------------------------------------------------
    # Defensive validation
    # ---------------------------------------------------------

    if not isinstance(out, list) or len(out) != 3:
        return fallback

    required_keys = {
        "name",
        "what_to_do",
        "why_it_may_help",
        "resources",
        "timing",
        "potential_benefit",
        "risks",
        "uncertainty",
        "evidence_ids",
    }

    valid_evidence_ids = {
        str(item.get("id"))
        for item in evidence
        if item.get("id")
    }

    for option in out:

        if not isinstance(option, dict):
            return fallback

        if set(option.keys()) != required_keys:
            return fallback

        # All main text fields must be strings.
        text_fields = {
            "name",
            "what_to_do",
            "why_it_may_help",
            "resources",
            "timing",
            "potential_benefit",
            "risks",
            "uncertainty",
        }

        for field in text_fields:
            if not isinstance(option.get(field), str):
                return fallback

        # Evidence IDs must be a list.
        evidence_ids = option.get("evidence_ids")

        if not isinstance(evidence_ids, list):
            return fallback

        # Prevent fabricated evidence IDs.
        for evidence_id in evidence_ids:
            if str(evidence_id) not in valid_evidence_ids:
                return fallback

        option["evidence_ids"] = [
            str(evidence_id)
            for evidence_id in evidence_ids
        ]

    return out
