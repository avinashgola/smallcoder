"""A tiny in-memory record store used by the article views."""

from core.errors import Conflict, NotFound, ValidationError

REQUIRED_FIELDS = ("title", "body")
ALLOWED_FIELDS = ("title", "body", "tags", "published")


class Repository:
    """Holds records keyed by an integer id handed out in order."""

    def __init__(self, seed=()):
        self._records = {}
        self._next_id = 1
        for record in seed:
            self.create(record)

    def __len__(self):
        return len(self._records)

    def __contains__(self, record_id):
        return record_id in self._records

    def validate(self, data):
        problems = {}
        for field in REQUIRED_FIELDS:
            value = data.get(field)
            if not isinstance(value, str) or not value.strip():
                problems[field] = "required"
        for field in data:
            if field not in ALLOWED_FIELDS:
                problems[field] = "unknown field"
        if problems:
            raise ValidationError(problems)

    def create(self, data):
        self.validate(data)
        if any(item["title"] == data["title"] for item in self._records.values()):
            raise Conflict("title %r already exists" % (data["title"],))
        record = {
            "id": self._next_id,
            "title": data["title"],
            "body": data["body"],
            "tags": sorted(data.get("tags", [])),
            "published": bool(data.get("published", False)),
        }
        self._records[record["id"]] = record
        self._next_id += 1
        return record

    def get(self, record_id):
        try:
            return self._records[record_id]
        except KeyError:
            raise NotFound("/articles/%s" % record_id) from None

    def update(self, record_id, changes):
        record = dict(self.get(record_id))
        record.update(changes)
        self.validate({k: v for k, v in record.items() if k != "id"})
        record["tags"] = sorted(record.get("tags", []))
        self._records[record_id] = record
        return record

    def delete(self, record_id):
        record = self.get(record_id)
        del self._records[record_id]
        return record

    def list(self, tag=None, published=None, limit=None, offset=0):
        """Records in id order, optionally filtered and paged."""
        items = [self._records[key] for key in sorted(self._records)]
        if tag is not None:
            items = [item for item in items if tag in item["tags"]]
        if published is not None:
            items = [item for item in items if item["published"] is published]
        items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items


SEED = [
    {"title": "Routing basics", "body": "How the table works.",
     "tags": ["routing", "intro"], "published": True},
    {"title": "Converters", "body": "Typed path segments.",
     "tags": ["routing"], "published": True},
    {"title": "Draft notes", "body": "Not finished yet.", "tags": []},
]
