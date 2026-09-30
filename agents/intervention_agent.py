from utils.llm import ask_llm_json

def _build_fallback():
"""
Safe fallback alternatives used when the LLM response is invalid
or when sufficient evidence is not available.
"""

```
return [
    {
        "name": "Verify the suspected field condition",
        "what_to_do": (
            "Inspect representative plants and the root-zone condition. "
            "Check whether the reported symptoms are widespread or localized "
            "and verify the relevant farm condition before applying an input."
        ),
        "why_it_may_help": (
            "Field verification can help distinguish among possible causes "
            "before resources are committed to a specific intervention."
        ),
        "resources": (
            "Farmer or labor time, basic field inspection, and local "
            "agricultural advice if available."
        ),
        "timing": "As soon as practical.",
        "potential_benefit": (
            "May reduce the risk of responding to the wrong underlying cause."
        ),
        "risks": (
            "Inspection requires time, and delaying action may matter if "
            "the crop is experiencing rapidly worsening stress."
        ),
        "uncertainty": (
            "The underlying cause has not been confirmed from the available information."
        ),
        "evidence_ids": [],
    },
    {
        "name": "Adjust management based on verified conditions",
        "what_to_do": (
            "After field verification, make a targeted management adjustment "
            "that addresses the condition actually observed, while avoiding "
            "unnecessary inputs."
        ),
        "why_it_may_help": (
            "A targeted response can address a verified farm constraint "
            "without assuming that the initial hypothesis is correct."
        ),
        "resources": (
            "Available farm resources, labor, water or other inputs depending "
            "on the verified condition."
        ),
        "timing": "After field verification.",
        "potential_benefit": (
            "May improve crop conditions when the suspected constraint is "
            "confirmed."
        ),
        "risks": (
            "An inappropriate adjustment may have little benefit or could "
            "create additional stress."
        ),
        "uncertainty": (
            "The appropriate management response depends on the field "
            "condition and crop stage."
        ),
        "evidence_ids": [],
    },
    {
        "name": "Monitor before committing additional resources",
        "what_to_do": (
            "Record symptom progression, affected area, soil or water "
            "conditions and recent management actions. Monitor representative "
            "plants before making a larger intervention where conditions allow."
        ),
        "why_it_may_help": (
            "Additional observations can provide information for comparing "
            "possible causes and deciding whether further intervention is justified."
        ),
        "resources": (
            "Farmer or labor time and simple field observations."
        ),
        "timing": "Over the next 24–72 hours, depending on crop condition.",
        "potential_benefit": (
            "Can reduce unnecessary expenditure when the cause remains uncertain."
        ),
        "risks": (
            "Monitoring without intervention may allow damage to progress "
            "if severe stress is already present."
        ),
        "uncertainty": (
            "The value of monitoring depends on how quickly the reported "
            "condition is changing."
        ),
        "evidence_ids": [],
    },
]
```

def _format_research_evidence(evidence, evidence_analysis):
"""
Convert automatically retrieved research evidence and its assessment
into a compact format for the intervention LLM.

```
The intervention agent is not allowed to create or modify citations.
"""

if not evidence:
    return (
        "No external research records were retrieved. "
        "Do not invent or imply research citations."
    )

analysis_by_id = {}

if isinstance(evidence_analysis, dict):
    assessments = evidence_analysis.get("assessments", [])

    if isinstance(assessments, list):
        for assessment in assessments:
            if not isinstance(assessment, dict):
                continue

            evidence_id = assessment.get("evidence_id")

            if evidence_id:
                analysis_by_id[str(evidence_id)] = assessment

formatted = []

for item in evidence:
    if not isinstance(item, dict):
        continue

    evidence_id = str(item.get("id", "")).strip()

    if not evidence_id:
        continue

    title = item.get("title", "Untitled research record")
    authors = item.get("authors_text", item.get("authors", ""))
    year = item.get("year", "")
    journal = item.get("journal", "")
    doi = item.get("doi", "")
    url = item.get("url", "")
    abstract = item.get("abstract", "")

    assessment = analysis_by_id.get(evidence_id, {})

    support_level = assessment.get(
        "support_level",
        item.get("support_level", "Unassessed"),
    )

    relevance = assessment.get(
        "relevance",
        item.get("relevance", ""),
    )

    why_relevant = assessment.get(
        "why_relevant",
        item.get("why_relevant", ""),
    )

    formatted.append(
        f"""
```

Evidence ID: {evidence_id}
Title: {title}
Authors: {authors}
Year: {year}
Journal: {journal}
DOI: {doi}
Source URL: {url}
Relevance: {relevance}
Support level: {support_level}
Why relevant: {why_relevant}
Abstract: {abstract}
""".strip()
)

```
if not formatted:
    return (
        "No usable external research records were available. "
        "Do not invent citations."
    )

return "\n\n".join(formatted)
```

def run_intervention_agent(
farm,
context,
weather,
crop_reasoning,
evidence=None,
evidence_analysis=None,
):
"""
Intervention Agent.

```
Generates exactly three practical, non-ranked intervention alternatives.

Research evidence is supplied dynamically at runtime. The agent may only
reference evidence IDs that actually exist in that supplied evidence.

The agent must not:
- invent citations,
- diagnose the crop with certainty,
- rank alternatives,
- invent field observations,
- or prescribe unsupported chemical treatments.
"""

fallback = _build_fallback()

if not isinstance(evidence, list):
    evidence = []

evidence_text = _format_research_evidence(
    evidence=evidence,
    evidence_analysis=evidence_analysis,
)

valid_evidence_ids = {
    str(item.get("id"))
    for item in evidence
    if isinstance(item, dict) and item.get("id")
}

prompt = f"""
```

You are the Intervention Agent for AGRODECISION PK.

Your task is to generate exactly THREE practical intervention alternatives
for the Pakistani farm described below.

The system follows this principle:

AI INVESTIGATES.
AI COMPARES.
HUMAN DECIDES.

The alternatives must therefore be presented for human comparison.
Do not select, rank, score, or recommend one alternative as the winner.

RETURN FORMAT

Return valid JSON containing either:

1. A JSON array containing exactly 3 objects

OR

2. An object with one key "options" containing an array of exactly 3 objects.

Each option MUST contain exactly these fields:

* name
* what_to_do
* why_it_may_help
* resources
* timing
* potential_benefit
* risks
* uncertainty
* evidence_ids

"evidence_ids" MUST be a list.

EVIDENCE RULES

Only use evidence IDs that appear in the AUTOMATICALLY RETRIEVED
RESEARCH EVIDENCE section.

Do NOT create evidence IDs.

Do NOT invent:

* papers
* authors
* journals
* years
* DOIs
* URLs
* statistics
* treatment effects
* application rates
* research findings

If no supplied evidence directly supports an intervention, use:

"evidence_ids": []

An evidence record being retrieved does NOT automatically mean that it
supports the intervention. Use the supplied support assessment carefully.

Do not make a stronger scientific claim than the supplied evidence supports.

Research conducted in another:

* country,
* climate,
* crop variety,
* season,
* production system,
* soil type,
* or experimental setting

does not guarantee the same result on this farm.

INTERVENTION RULES

1. Generate exactly three alternatives.

2. Do NOT rank the alternatives.

3. Do NOT call any alternative:

   * best
   * preferred
   * optimal
   * most effective
   * recommended
   * first choice

4. Do not provide an overall winner.

5. Do not claim that a biological cause is confirmed.

6. Keep interventions conditional on appropriate field verification.

7. Do not invent field observations.

8. Consider:

   * crop
   * crop stage if available
   * reported symptoms
   * affected area
   * duration
   * soil
   * water availability
   * weather
   * farm size
   * labor
   * budget
   * Pakistani farming conditions

9. Do not prescribe pesticides, fungicides, herbicides, fertilizers,
   growth regulators, or other chemical treatments unless the supplied
   evidence and farm information provide adequate support.

10. If a chemical or input-based intervention is discussed, keep it
    conditional and advise appropriate local verification rather than
    inventing a dose or application rate.

11. At least one alternative should be verification-first or
    monitoring-oriented when the cause remains materially uncertain.

12. Explain uncertainty honestly.

13. The human user remains responsible for the final farm decision.

FARM INFORMATION
{farm}

AGRICULTURAL CONTEXT
{context}

WEATHER
{weather}

CROP AND BIOLOGICAL REASONING
{crop_reasoning}

AUTOMATICALLY RETRIEVED RESEARCH EVIDENCE
{evidence_text}
"""

```
out = ask_llm_json(prompt, fallback)

# ---------------------------------------------------------
# Normalize {"options": [...]} responses
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

for option in out:

    if not isinstance(option, dict):
        return fallback

    if set(option.keys()) != required_keys:
        return fallback

    # All narrative fields must be strings.
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

    # Normalize IDs to strings.
    option["evidence_ids"] = [
        str(evidence_id)
        for evidence_id in evidence_ids
    ]

return out
```
