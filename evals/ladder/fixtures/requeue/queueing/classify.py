"""Deciding which failures deserve another attempt."""

from queueing.errors import PermanentError, TransientError


class Classifier:
    """Sorts exceptions into retryable and permanent."""

    def __init__(self, retryable=(TransientError,), permanent=(PermanentError,),
                 default_retryable=True):
        self.retryable = tuple(retryable)
        self.permanent = tuple(permanent)
        self.default_retryable = bool(default_retryable)

    def is_retryable(self, error):
        """True when another attempt could plausibly succeed."""
        if error is None:
            return False
        if isinstance(error, self.permanent):
            return False
        if isinstance(error, self.retryable):
            return True
        return self.default_retryable

    def retry_after(self, error):
        """A delay the failure itself asked for, if any."""
        value = getattr(error, "retry_after", None)
        if value is None:
            return None
        if value < 0:
            raise ValueError("retry_after cannot be negative")
        return float(value)

    def with_permanent(self, *types):
        """A copy that also treats `types` as permanent failures."""
        return Classifier(
            retryable=self.retryable,
            permanent=self.permanent + tuple(types),
            default_retryable=self.default_retryable,
        )

    def describe(self):
        names = lambda group: ", ".join(t.__name__ for t in group) or "none"
        return "retry %s; never retry %s; unknown errors %s" % (
            names(self.retryable),
            names(self.permanent),
            "retried" if self.default_retryable else "dropped",
        )


DEFAULT_CLASSIFIER = Classifier()
STRICT_CLASSIFIER = Classifier(default_retryable=False)
