"""What one flag decides for one subject."""

from .bucket import in_rollout
from .errors import FlagDefinitionError

KEYS = ("enabled", "percent", "allow", "deny")


class Flag:
    """A named feature with a rollout percentage and two override lists.

    The decision order is: a flag that is switched off is off for everybody;
    then the deny list, then the allow list, then the rollout itself.
    """

    def __init__(self, name, enabled=True, percent=0, allow=(), deny=()):
        if not 0 <= percent <= 100:
            raise FlagDefinitionError(f"{name}: percent {percent} is out of range")
        overlap = sorted(set(allow) & set(deny))
        if overlap:
            raise FlagDefinitionError(f"{name}: {overlap} are both allowed and denied")
        self.name = name
        self.enabled = enabled
        self.percent = percent
        self.allow = frozenset(allow)
        self.deny = frozenset(deny)

    @classmethod
    def from_dict(cls, name, body):
        unknown = sorted(set(body) - set(KEYS))
        if unknown:
            raise FlagDefinitionError(f"{name}: unknown settings {unknown}")
        return cls(name, **body)

    def decide(self, subject):
        if not self.enabled:
            return False
        if subject in self.deny:
            return False
        if subject in self.allow:
            return True
        return in_rollout(self.name, subject, self.percent)

    def __repr__(self):
        state = "on" if self.enabled else "off"
        return f"Flag({self.name!r}, {state}, {self.percent}%)"
