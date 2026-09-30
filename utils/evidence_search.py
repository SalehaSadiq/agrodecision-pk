"""
Automatic research evidence retrieval for AGRODECISION PK.

This module searches OpenAlex for real scientific publications based on:
    - crop
    - agricultural problem / symptom
    - relevant context
    - optional additional search terms

Important:
- This module retrieves publication metadata from an external research API.
- It does NOT invent papers, authors, journals, DOIs, or URLs.
- It does NOT decide whether a paper proves a claim.
- Evidence interpretation is handled separately by the Evidence Agent.
- The module is designed to work in Streamlit Cloud without local databases.

OpenAlex:
https://openalex.org/

API endpoint:
https://api.openalex.org/works
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests


OPENALEX_API_URL = "https://api.openalex.org/works"

# Keep the request reasonably small for a hackathon application.
DEFAULT_MAX_RESULTS = 6

# OpenAlex normally responds quickly, but a timeout prevents the Streamlit
# application from hanging indefinitely if the external service is unavailable.
DEFAULT_TIMEOUT = 12

# Optional polite-pool identification.
#
# If OPENALEX_EMAIL is supplied as an environment variable, it is included
# as a mailto parameter. The application still works without it.
DEFAULT_USER_AGENT = "AGRODECISION-PK/1.0"


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def _clean_text(value: Any) -> str:
    """
    Convert a value to clean text.

    Returns an empty string for None or unusable values.
    """

    if value is None:
        return ""

    text = str(value)

    # Collapse repeated whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _normalize_text(value: Any) -> str:
    """
    Normalize text for comparison and deduplication.
    """

    text = _clean_text(value).lower()

    # Remove punctuation while preserving letters/numbers.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Collapse whitespace again.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _first_non_empty(*values: Any) -> str:
    """
    Return the first non-empty value.
    """

    for value in values:
        cleaned = _clean_text(value)

        if cleaned:
            return cleaned

    return ""


# ---------------------------------------------------------------------------
# Crop / query construction
# ---------------------------------------------------------------------------


def _extract_crop(farm: Optional[Dict[str, Any]]) -> str:
    """
    Extract crop name from the farm dictionary.

    Supports the field names already used by the project.
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
            return _clean_text(value)

    return ""


def _extract_problem_text(
    farm: Optional[Dict[str, Any]],
    context: Any = None,
) -> str:
    """
    Extract farmer-reported problem/symptom information.

    The function is intentionally flexible because the application may
    represent farmer inputs using different field names.
    """

    parts: List[str] = []

    if isinstance(farm, dict):

        possible_problem_keys = [
            "problem",
            "symptom",
            "symptoms",
            "issue",
            "description",
            "main_symptom",
            "main symptom",
            "crop_problem",
            "crop problem",
            "observed_problem",
            "observed problem",
        ]

        for key in possible_problem_keys:
            value = farm.get(key)

            if value:
                parts.append(_clean_text(value))

    # Context may be a dictionary or plain text.
    if isinstance(context, dict):

        possible_context_keys = [
            "problem",
            "symptom",
            "symptoms",
            "issue",
            "description",
            "risk",
            "risk_factors",
            "risk factors",
        ]

        for key in possible_context_keys:
            value = context.get(key)

            if value:
                parts.append(_clean_text(value))

    elif context:
        parts.append(_clean_text(context))

    # Remove duplicates while preserving order.
    unique_parts = []

    seen = set()

    for part in parts:
        normalized = _normalize_text(part)

        if not normalized:
            continue

        if normalized not in seen:
            seen.add(normalized)
            unique_parts.append(part)

    return " ".join(unique_parts)


def _extract_weather_terms(weather: Any) -> str:
    """
    Extract useful weather/context terms from the weather result.

    We do not send every weather field to the research API. Only a small
    number of terms that may help retrieve relevant agricultural literature
    are used.
    """

    if not isinstance(weather, dict):
        return ""

    terms = []

    mapping = {
        "temperature": "temperature",
        "temp": "temperature",
        "humidity": "humidity",
        "relative_humidity": "relative humidity",
        "relative humidity": "relative humidity",
        "rainfall": "rainfall",
        "rain": "rainfall",
        "precipitation": "precipitation",
        "wind_speed": "wind",
        "wind speed": "wind",
    }

    for key, label in mapping.items():

        if key not in weather:
            continue

        value = weather.get(key)

        if value is None or value == "":
            continue

        terms.append(f"{label} {value}")

    return " ".join(terms)


def _build_search_query(
    crop: str,
    problem: str,
    context: Any = None,
    weather: Any = None,
    extra_terms: Optional[List[str]] = None,
) -> str:
    """
    Build a focused research query.

    The goal is not to create a huge natural-language prompt. A compact
    query generally gives cleaner literature retrieval.
    """

    parts: List[str] = []

    if crop:
        parts.append(crop)

    if problem:
        # Limit extremely long farmer descriptions.
        problem_words = problem.split()

        if len(problem_words) > 18:
            problem = " ".join(problem_words[:18])

        parts.append(problem)

    weather_terms = _extract_weather_terms(weather)

    if weather_terms:
        parts.append(weather_terms)

    if context:
        if isinstance(context, dict):

            risk_terms = []

            for key in [
                "risk",
                "risk_factors",
                "risk factors",
                "climate",
                "stress",
            ]:
                value = context.get(key)

                if value:
                    risk_terms.append(_clean_text(value))

            if risk_terms:
                parts.extend(risk_terms[:2])

    if extra_terms:
        for term in extra_terms:
            cleaned = _clean_text(term)

            if cleaned:
                parts.append(cleaned)

    query = " ".join(parts)

    # Prevent excessively long requests.
    words = query.split()

    if len(words) > 45:
        query = " ".join(words[:45])

    return query.strip()


# ---------------------------------------------------------------------------
# OpenAlex API
# ---------------------------------------------------------------------------


def _make_openalex_params(
    query: str,
    max_results: int,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Construct OpenAlex request parameters.
    """

    params: Dict[str, Any] = {
        "search": query,
        "per-page": max(1, min(int(max_results), 25)),
        "sort": "relevance_score:desc",
        "select": (
            "id,doi,title,display_name,publication_year,"
            "publication_date,primary_location,"
            "authorships,host_venue,abstract_inverted_index,"
            "type,cited_by_count"
        ),
    }

    if email:
        params["mailto"] = email

    return params


def _request_openalex(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    timeout: int = DEFAULT_TIMEOUT,
    email: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Query OpenAlex and return raw work records.

    Returns an empty list if the external API cannot be reached or returns
    an invalid response.
    """

    if not query:
        return []

    params = _make_openalex_params(
        query=query,
        max_results=max_results,
        email=email,
    )

    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            OPENALEX_API_URL,
            params=params,
            headers=headers,
            timeout=timeout,
        )

        response.raise_for_status()

        data = response.json()

    except (
        requests.RequestException,
        ValueError,
    ):
        return []

    if not isinstance(data, dict):
        return []

    results = data.get("results")

    if not isinstance(results, list):
        return []

    return [
        item
        for item in results
        if isinstance(item, dict)
    ]


# ---------------------------------------------------------------------------
# Abstract reconstruction
# ---------------------------------------------------------------------------


def _reconstruct_abstract(
    abstract_inverted_index: Any,
) -> str:
    """
    Reconstruct an abstract from OpenAlex's inverted-index representation.

    OpenAlex may provide abstracts as:
        {
            "word": [0, 5],
            "another": [1]
        }

    This function converts that structure back into readable text.
    """

    if not isinstance(abstract_inverted_index, dict):
        return ""

    positions: List[tuple[int, str]] = []

    for word, indexes in abstract_inverted_index.items():

        if not isinstance(indexes, list):
            continue

        for index in indexes:

            if not isinstance(index, int):
                continue

            positions.append((index, str(word)))

    if not positions:
        return ""

    positions.sort(key=lambda item: item[0])

    words = [word for _, word in positions]

    return " ".join(words)


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------


def _extract_authors(work: Dict[str, Any]) -> List[str]:
    """
    Extract author names from an OpenAlex work.
    """

    authorships = work.get("authorships")

    if not isinstance(authorships, list):
        return []

    authors: List[str] = []

    for authorship in authorships:

        if not isinstance(authorship, dict):
            continue

        author = authorship.get("author")

        if not isinstance(author, dict):
            continue

        display_name = _clean_text(
            author.get("display_name")
        )

        if display_name:
            authors.append(display_name)

    return authors


def _extract_journal(work: Dict[str, Any]) -> str:
    """
    Extract journal/source title.
    """

    host_venue = work.get("host_venue")

    if not isinstance(host_venue, dict):
        return ""

    return _first_non_empty(
        host_venue.get("display_name"),
        host_venue.get("publisher"),
    )


def _extract_source_url(work: Dict[str, Any]) -> str:
    """
    Extract a useful public URL.

    Preference:
    1. DOI
    2. OpenAlex record
    """

    doi = _clean_text(work.get("doi"))

    if doi:
        if doi.startswith("https://doi.org/"):
            return doi

        if doi.startswith("http://doi.org/"):
            return doi.replace(
                "http://doi.org/",
                "https://doi.org/",
            )

        if doi.startswith("doi.org/"):
            return f"https://{doi}"

        return f"https://doi.org/{doi}"

    openalex_id = _clean_text(work.get("id"))

    if openalex_id:
        return openalex_id

    return ""


def _extract_doi(work: Dict[str, Any]) -> str:
    """
    Extract and normalize DOI.
    """

    doi = _clean_text(work.get("doi"))

    if not doi:
        return ""

    doi = doi.replace(
        "https://doi.org/",
        "",
    )

    doi = doi.replace(
        "http://doi.org/",
        "",
    )

    doi = doi.replace(
        "doi:",
        "",
    )

    return doi.strip()


def _normalize_work(
    work: Dict[str, Any],
    evidence_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Convert a raw OpenAlex work into the standardized evidence structure
    used by AGRODECISION PK.
    """

    if not isinstance(work, dict):
        return None

    title = _first_non_empty(
        work.get("display_name"),
        work.get("title"),
    )

    if not title:
        return None

    authors = _extract_authors(work)

    journal = _extract_journal(work)

    year = work.get("publication_year")

    try:
        year = int(year) if year else None
    except (TypeError, ValueError):
        year = None

    doi = _extract_doi(work)

    url = _extract_source_url(work)

    abstract = _reconstruct_abstract(
        work.get("abstract_inverted_index")
    )

    publication_date = _clean_text(
        work.get("publication_date")
    )

    source_type = "peer_reviewed_research"

    work_type = _clean_text(
        work.get("type")
    )

    return {
        "id": evidence_id,
        "source_type": source_type,
        "source_name": "OpenAlex",
        "title": title,
        "authors": authors,
        "authors_text": ", ".join(authors),
        "year": year,
        "publication_date": publication_date,
        "journal": journal,
        "doi": doi,
        "url": url,
        "abstract": abstract,
        "work_type": work_type,
        "cited_by_count": work.get("cited_by_count", 0),
        "openalex_id": _clean_text(work.get("id")),
        "evidence_strength": "Not yet assessed",
        "claim_supported": "",
        "information_used": "",
        "retrieval_query": "",
    }


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def _deduplicate_evidence(
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove duplicate publications.

    DOI is preferred as the unique identifier. If DOI is unavailable,
    normalized title is used.
    """

    unique: List[Dict[str, Any]] = []

    seen_dois = set()
    seen_titles = set()

    for item in evidence:

        doi = _normalize_text(
            item.get("doi")
        )

        title = _normalize_text(
            item.get("title")
        )

        if doi:

            if doi in seen_dois:
                continue

            seen_dois.add(doi)

        elif title:

            if title in seen_titles:
                continue

            seen_titles.add(title)

        else:
            continue

        unique.append(item)

    return unique


# ---------------------------------------------------------------------------
# Public search functions
# ---------------------------------------------------------------------------


def search_research(
    crop: str = "",
    problem: str = "",
    context: Any = None,
    weather: Any = None,
    extra_terms: Optional[List[str]] = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    timeout: int = DEFAULT_TIMEOUT,
    email: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search for real scientific publications relevant to the agricultural case.

    Parameters
    ----------
    crop:
        Crop name, e.g. "tomato".

    problem:
        Farmer-reported symptom/problem, e.g.
        "brown lesions on leaves".

    context:
        Agricultural context. Can be a dictionary or text.

    weather:
        Weather information. Only selected fields are used in the search.

    extra_terms:
        Optional additional research terms.

    max_results:
        Maximum number of records requested.

    timeout:
        HTTP timeout in seconds.

    email:
        Optional email address for OpenAlex polite-pool identification.

    Returns
    -------
    list of dict
        Standardized, deduplicated evidence records.

    Important:
        An empty list means no usable records were retrieved. It does not
        mean that no scientific literature exists.
    """

    crop = _clean_text(crop)
    problem = _clean_text(problem)

    query = _build_search_query(
        crop=crop,
        problem=problem,
        context=context,
        weather=weather,
        extra_terms=extra_terms,
    )

    if not query:
        return []

    raw_results = _request_openalex(
        query=query,
        max_results=max_results,
        timeout=timeout,
        email=email,
    )

    evidence: List[Dict[str, Any]] = []

    for index, work in enumerate(raw_results, start=1):

        evidence_id = f"LIVE-{index:03d}"

        normalized = _normalize_work(
            work=work,
            evidence_id=evidence_id,
        )

        if normalized is None:
            continue

        normalized["retrieval_query"] = query

        evidence.append(normalized)

    evidence = _deduplicate_evidence(evidence)

    # Re-number after deduplication so IDs remain sequential.
    for index, item in enumerate(evidence, start=1):
        item["id"] = f"LIVE-{index:03d}"

    return evidence


def search_for_farm(
    farm: Optional[Dict[str, Any]],
    context: Any = None,
    weather: Any = None,
    extra_terms: Optional[List[str]] = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    timeout: int = DEFAULT_TIMEOUT,
    email: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience wrapper for the AGRODECISION PK agent workflow.

    Instead of manually supplying crop/problem separately, this function
    extracts them from the existing farm dictionary.
    """

    crop = _extract_crop(farm)

    problem = _extract_problem_text(
        farm=farm,
        context=context,
    )

    return search_research(
        crop=crop,
        problem=problem,
        context=context,
        weather=weather,
        extra_terms=extra_terms,
        max_results=max_results,
        timeout=timeout,
        email=email,
    )


def search_by_query(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    timeout: int = DEFAULT_TIMEOUT,
    email: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Direct research search when an agent has already constructed a query.

    Example:
        search_by_query(
            "tomato late blight humidity leaf wetness"
        )
    """

    query = _clean_text(query)

    if not query:
        return []

    raw_results = _request_openalex(
        query=query,
        max_results=max_results,
        timeout=timeout,
        email=email,
    )

    evidence: List[Dict[str, Any]] = []

    for index, work in enumerate(raw_results, start=1):

        normalized = _normalize_work(
            work=work,
            evidence_id=f"LIVE-{index:03d}",
        )

        if normalized is None:
            continue

        normalized["retrieval_query"] = query

        evidence.append(normalized)

    evidence = _deduplicate_evidence(evidence)

    for index, item in enumerate(evidence, start=1):
        item["id"] = f"LIVE-{index:03d}"

    return evidence


def get_evidence_summary(
    evidence: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Create a compact representation for passing retrieved evidence
    into an LLM prompt.

    The complete evidence records remain available for the final report.
    """

    summaries: List[Dict[str, Any]] = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        summaries.append(
            {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "authors": item.get("authors_text", ""),
                "year": item.get("year"),
                "journal": item.get("journal", ""),
                "doi": item.get("doi", ""),
                "url": item.get("url", ""),
                "abstract": item.get("abstract", ""),
            }
        )

    return summaries


def format_evidence_for_prompt(
    evidence: List[Dict[str, Any]],
) -> str:
    """
    Format retrieved evidence for an LLM prompt.

    The prompt explicitly labels the records as RETRIEVED evidence so that
    downstream agents can be instructed to use only these records and never
    invent citations.
    """

    if not evidence:
        return (
            "No external research records were retrieved for this case. "
            "Do not invent or fabricate citations."
        )

    sections: List[str] = []

    for item in evidence:

        evidence_id = _clean_text(
            item.get("id")
        )

        title = _clean_text(
            item.get("title")
        )

        authors = _clean_text(
            item.get("authors_text")
        )

        year = item.get("year")

        journal = _clean_text(
            item.get("journal")
        )

        doi = _clean_text(
            item.get("doi")
        )

        url = _clean_text(
            item.get("url")
        )

        abstract = _clean_text(
            item.get("abstract")
        )

        # Keep prompts manageable.
        if len(abstract) > 2500:
            abstract = abstract[:2500] + "..."

        sections.append(
            "\n".join(
                [
                    f"Evidence ID: {evidence_id}",
                    f"Title: {title}",
                    f"Authors: {authors}",
                    f"Year: {year if year else 'Not available'}",
                    f"Journal: {journal or 'Not available'}",
                    f"DOI: {doi or 'Not available'}",
                    f"URL: {url or 'Not available'}",
                    f"Abstract: {abstract or 'Not available'}",
                ]
            )
        )

    return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Simple connectivity test
# ---------------------------------------------------------------------------


def test_evidence_search(
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Perform a small API connectivity test.

    This is useful for testing the Streamlit deployment without involving
    the rest of the agent pipeline.
    """

    test_query = "tomato plant disease"

    try:

        results = _request_openalex(
            query=test_query,
            max_results=1,
            timeout=timeout,
        )

        return {
            "success": True,
            "results_found": len(results),
            "message": (
                "OpenAlex research search is reachable."
            ),
        }

    except Exception as exc:
        # Defensive final safeguard.
        return {
            "success": False,
            "results_found": 0,
            "message": str(exc),
        }
