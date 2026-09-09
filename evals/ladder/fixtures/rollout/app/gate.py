"""The calls the rest of the application makes."""

from flags.audit import report
from flags.errors import UnknownFlag

from .flagset import REGISTRY


def can_use(subject, feature):
    """True when ``feature`` is on for this account."""
    return REGISTRY.is_on(feature, subject)


def active_features(subject):
    """Every feature that is on for this account, in a stable order."""
    return REGISTRY.enabled_for(subject)


def why(subject, feature):
    """The one-line explanation shown on the support screen."""
    return report(REGISTRY, subject)[REGISTRY.names().index(feature)]


def require(subject, feature):
    """Raise unless the account has the feature."""
    if feature not in REGISTRY:
        raise UnknownFlag(feature)
    if not can_use(subject, feature):
        raise PermissionError(f"{feature} is not available for {subject}")


def status_page():
    """What the internal status page shows about rollouts in progress."""
    return REGISTRY.rollout_plan()
