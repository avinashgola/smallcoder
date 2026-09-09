from queueing.backoff import Backoff
from queueing.classify import STRICT_CLASSIFIER
from queueing.errors import PermanentError, TransientError
from queueing.policy import NO_RETRY, RetryPolicy
from queueing.task import Task

BOOM = TransientError("service unavailable")


def policy(max_attempts=3):
    return RetryPolicy(max_attempts=max_attempts,
                       backoff=Backoff(base=1.0, factor=2.0, cap=60.0))


def test_a_fresh_failure_is_retried():
    assert policy().should_retry(1, BOOM) is True
    assert policy().should_retry(2, BOOM) is True


def test_the_budget_counts_the_first_try():
    assert policy(max_attempts=3).should_retry(3, BOOM) is False


def test_a_single_attempt_policy_never_retries():
    assert policy(max_attempts=1).should_retry(1, BOOM) is False
    assert NO_RETRY.should_retry(1, BOOM) is False


def test_permanent_failures_are_never_retried():
    assert policy().should_retry(1, PermanentError("bad payload")) is False


def test_unknown_errors_follow_the_classifier():
    lenient = policy()
    strict = policy().with_classifier(STRICT_CLASSIFIER)
    assert lenient.should_retry(1, ValueError("odd")) is True
    assert strict.should_retry(1, ValueError("odd")) is False


def test_attempts_left():
    assert policy(max_attempts=3).attempts_left(1) == 2
    assert policy(max_attempts=3).attempts_left(3) == 0


def test_delay_uses_the_backoff():
    assert policy().delay_for(1) == 1.0
    assert policy().delay_for(3) == 4.0


def test_error_can_ask_for_its_own_delay():
    assert policy().delay_for(1, TransientError("busy", retry_after=0.25)) == 0.25


def test_task_override_replaces_the_budget():
    base = policy(max_attempts=3)
    assert base.for_task(Task("t", "email")).max_attempts == 3
    assert base.for_task(Task("t", "email", max_attempts=5)).max_attempts == 5
    assert base.for_task(Task("t", "email", max_attempts=3)) is base


def test_schedule_lists_one_delay_per_retry():
    assert policy(max_attempts=3).schedule() == [1.0, 2.0]
    assert policy(max_attempts=1).schedule() == []


def test_from_config():
    built = RetryPolicy.from_config({"max_attempts": 4, "base_delay": 2.0,
                                     "factor": 2.0, "cap": 100.0})
    assert built.max_attempts == 4
    assert built.schedule() == [2.0, 4.0, 8.0]


def test_describe_mentions_the_budget():
    assert "up to 3 attempts" in policy().describe()
