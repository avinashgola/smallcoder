"""flags -- percentage rollouts and allow/deny lists for feature flags.

Nothing here touches a clock or a random number generator: a subject always
lands in the same bucket, so a rollout that grows never takes the feature away
from anyone who already had it.
"""

from .audit import explain, report
from .bucket import bucket_of, in_rollout, share
from .errors import FlagDefinitionError, FlagError, UnknownFlag
from .registry import Registry, parse_definitions
from .rules import Flag

__all__ = [
    "explain",
    "report",
    "bucket_of",
    "in_rollout",
    "share",
    "FlagDefinitionError",
    "FlagError",
    "UnknownFlag",
    "Registry",
    "parse_definitions",
    "Flag",
]
