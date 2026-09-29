from datetime import datetime


class EvidenceTracker:
    """
    Tracks the evidence used by AGRODECISION PK.

    Evidence can come from external public sources, farmer-provided
    information, demo assumptions, or AI interpretation.
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
        }

        self.items.append(item)

        return item
