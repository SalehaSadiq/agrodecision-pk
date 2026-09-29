from datetime import datetime


class EvidenceTracker:

    def __init__(self):
        self.items = []

    def add(
        self,
        source_type,
        source_name,
        title,
        url,
        claim_supported,
        information_used,
        data_timestamp="",
    ):

        item = {
            "source_type": source_type,
            "source_name": source_name,
            "title": title,
            "url": url,
            "accessed_at": datetime.now().isoformat(
                timespec="seconds"
            ),
            "data_timestamp": data_timestamp,
            "claim_supported": claim_supported,
            "information_used": information_used,
        }

        self.items.append(item)

        return item
