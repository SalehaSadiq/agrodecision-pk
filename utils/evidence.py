from datetime import datetime


class EvidenceTracker:
    """
    Tracks evidence used by AGRODECISION PK.

    Evidence may come from:
    - peer-reviewed research studies
    - official/public agricultural sources
    - weather/data providers
    - farmer-provided information
    - demo assumptions
    - AI interpretation
    """

    def __init__(self):
        self.items = []

    def add(
        self,
        source_type,
        source_name,
        title,
        url="",
        claim_supported="",
        information_used="",
        data_timestamp="",
        authors="",
        year="",
        journal="",
        doi="",
        evidence_strength="",
        agent="",
    ):
        item = {
            "source_type": str(source_type),
            "source_name": str(source_name),
            "title": str(title),
            "url": str(url) if url else "",
            "accessed_at": datetime.now().isoformat(
                timespec="seconds"
            ),
            "data_timestamp": str(data_timestamp)
            if data_timestamp
            else "",
            "claim_supported": str(claim_supported),
            "information_used": str(information_used),

            # Research citation metadata
            "authors": str(authors),
            "year": str(year),
            "journal": str(journal),
            "doi": str(doi),

            # Evidence interpretation
            "evidence_strength": str(evidence_strength),
            "agent": str(agent),
        }

        self.items.append(item)

        return item

    def get_items(self):
        return self.items

    def clear(self):
        self.items = []
