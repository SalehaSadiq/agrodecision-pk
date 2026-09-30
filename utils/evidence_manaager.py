import json
from pathlib import Path


EVIDENCE_FILE = Path("data/evidence_sources.json")


def load_evidence():
    if not EVIDENCE_FILE.exists():
        return []

    with open(EVIDENCE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def find_evidence(crop=None, topic=None):
    evidence = load_evidence()

    matches = []

    for item in evidence:
        crop_match = (
            not crop
            or item.get("crop", "").lower() == crop.lower()
        )

        topic_match = (
            not topic
            or item.get("topic", "").lower() == topic.lower()
        )

        if crop_match and topic_match:
            matches.append(item)

    return matches


def format_citations(evidence):
    citations = []

    for i, item in enumerate(evidence, start=1):
        citations.append({
            "citation_number": i,
            "title": item.get("title"),
            "authors": item.get("authors"),
            "year": item.get("year"),
            "journal": item.get("journal"),
            "doi": item.get("doi"),
            "url": item.get("url"),
            "evidence_strength": item.get("evidence_strength")
        })

    return citations
