import json
from pathlib import Path

from utils.llm import ask_llm_json


EVIDENCE_FILE = Path("data/evidence_sources.json")


def _load_evidence():
    """
    Load verified agricultural evidence from the local evidence database.

    If the evidence file is missing, invalid, or empty, the agent continues
    safely without external research evidence.
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
    Try to identify the crop from the farm information.

    Supports several possible field names so the agent remains compatible
    with different versions of the application.
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
    Select evidence relevant to the reported crop.

    Evidence marked as 'general' is also included.

    The LLM is only given evidence that already exists in the
    verified evidence database.
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
    Convert verified evidence into a compact, readable format
    for the reasoning model.
    """

    if not evidence:
        return "No verified external research evidence is currently available."

    formatted = []

    for item in evidence:
        evidence_id = item.get("id", "UNKNOWN")

        title = item.get("title", "Untitled source")
        authors = item.get("authors", "")
        year = item.get("year", "")
        journal = item.get("journal", "")
        claim = item.get("claim", "")
        source_type = item.get("source_type", "")

        citation_parts = []

        if authors:
            citation_parts.append(str(authors))

        if year:
            citation_parts.append(f"({year})")

        citation = " ".join(citation_parts)

        formatted.append(
            f"""
Evidence ID: {evidence_id}
Source type: {source_type}
Citation: {citation}
Title: {title}
Journal: {journal}
Supported claim: {claim}
""".strip()
        )

    return "\n\n".join(formatted)


def _build_fallback():
    """
    Safe fallback response used when the LLM response is invalid.
    """

    return {
        "summary": (
            "The reported symptoms are compatible with more than one "
            "explanation. The system therefore treats these as hypotheses "
            "rather than a diagnosis."
        ),
        "possible_causes": [
            {
                "name": "Water stress or root-zone limitation",
                "confidence": "Moderate",
                "why": (
                    "The reported water situation and symptoms can be "
                    "consistent with inadequate water availability."
                ),
                "evidence_ids": [],
            },
            {
                "name": "Weather-related stress",
                "confidence": "Low",
                "why": (
                    "Recent temperature, rainfall and atmospheric "
                    "conditions can alter crop water demand and plant stress."
                ),
                "evidence_ids": [],
            },
            {
                "name": "Pest, disease or nutrient-related stress",
                "confidence": "Low",
                "why": (
                    "Similar visible symptoms can arise from biological "
                    "or nutritional causes and require field verification."
                ),
                "evidence_ids": [],
            },
        ],
    }


def run_crop_agent(farm, context, weather):
    """
    Crop & Biological Reasoning Agent.

    Produces three possible explanations as hypotheses, not a diagnosis.

    The agent uses:
    - farmer-provided information
    - agricultural context
    - available weather information
    - verified evidence from data/evidence_sources.json

    Research evidence is used to support or contextualize hypotheses.
    The model is explicitly prevented from inventing citations.
    """

    fallback = _build_fallback()

    evidence = _get_relevant_evidence(farm)
    evidence_text = _format_evidence_for_prompt(evidence)

    prompt = f"""
You are the Crop & Biological Reasoning Agent for AGRODECISION PK,
a human-in-the-loop agricultural decision-support system for Pakistan.

Your task is to analyze the farmer's information, agricultural context,
weather information, and VERIFIED research evidence.

You are NOT a diagnostic system.

Return valid JSON only.

The JSON must contain exactly these top-level keys:

- "summary"
- "possible_causes"

"possible_causes" must contain exactly 3 objects.

Each object must contain exactly these keys:

- "name"
- "confidence"
- "why"
- "evidence_ids"

The confidence value must be exactly one of:

- "Low"
- "Moderate"
- "High"

"evidence_ids" must be a list containing only Evidence IDs that appear
in the VERIFIED EVIDENCE section below.

If no supplied evidence supports a particular hypothesis, return:

"evidence_ids": []

IMPORTANT RULES:

1. These are hypotheses, NOT diagnoses.

2. Do not claim that any cause is confirmed.

3. Do not prescribe a treatment here.

4. Use the farmer-provided information and weather information.

5. Do not invent observations that were not provided.

6. Clearly reflect uncertainty.

7. Consider alternative explanations where appropriate.

8. The three possibilities must be meaningfully different.

9. Do not invent scientific studies.

10. Do not invent authors, journals, years, DOIs, URLs, statistics,
    thresholds, or other research findings.

11. You may ONLY refer to research evidence listed in the
    VERIFIED EVIDENCE section.

12. If the available evidence does not support a claim, do not
    manufacture evidence for it.

13. Research evidence does not prove that the hypothesis is occurring
    on this particular farm.

14. Distinguish between:
    - farmer observations
    - weather/context information
    - published research evidence
    - your interpretation

15. Keep the reasoning practical and understandable for a farmer
    or agricultural advisor.

16. Do not recommend pesticides, fertilizers, medicines, or other
    interventions in this agent.

17. The human user must remain responsible for verifying the situation
    before taking action.

FARM INFORMATION:
{farm}

AGRICULTURAL CONTEXT:
{context}

WEATHER INFORMATION:
{weather}

VERIFIED EVIDENCE:
{evidence_text}
"""

    result = ask_llm_json(prompt, fallback)

    # ---------------------------------------------------------
    # Defensive validation
    # ---------------------------------------------------------

    if not isinstance(result, dict):
        return fallback

    if not isinstance(result.get("summary"), str):
        return fallback

    causes = result.get("possible_causes")

    if not isinstance(causes, list) or len(causes) != 3:
        return fallback

    required_keys = {
        "name",
        "confidence",
        "why",
        "evidence_ids",
    }

    valid_confidence = {
        "Low",
        "Moderate",
        "High",
    }

    valid_evidence_ids = {
        str(item.get("id"))
        for item in evidence
        if item.get("id")
    }

    for cause in causes:

        if not isinstance(cause, dict):
            return fallback

        if set(cause.keys()) != required_keys:
            return fallback

        if not isinstance(cause.get("name"), str):
            return fallback

        if not isinstance(cause.get("why"), str):
            return fallback

        if cause.get("confidence") not in valid_confidence:
            return fallback

        evidence_ids = cause.get("evidence_ids")

        if not isinstance(evidence_ids, list):
            return fallback

        # Make sure the LLM cannot introduce fake evidence IDs.
        for evidence_id in evidence_ids:
            if str(evidence_id) not in valid_evidence_ids:
                return fallback

        # Normalize IDs to strings.
        cause["evidence_ids"] = [
            str(evidence_id)
            for evidence_id in evidence_ids
        ]

    return result
