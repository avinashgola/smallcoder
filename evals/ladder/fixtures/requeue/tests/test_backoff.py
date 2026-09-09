import pytest

from queueing.backoff import NO_BACKOFF, Backoff
from support.rng import ConstantJitter


def test_first_delay_is_the_base_delay():
    backoff = Backoff(base=0.5, factor=2.0, cap=30.0)
    assert backoff.delay_for(1) == 0.5


def test_delays_grow_by_the_factor():
    backoff = Backoff(base=1.0, factor=3.0, cap=100.0)
    assert backoff.series(4) == [1.0, 3.0, 9.0, 27.0]


def test_delays_are_capped():
    backoff = Backoff(base=1.0, factor=10.0, cap=20.0)
    assert backoff.series(4) == [1.0, 10.0, 20.0, 20.0]


def test_jitter_shortens_the_delay_deterministically():
    backoff = Backoff(base=4.0, factor=1.0, cap=10.0, jitter=0.5,
                      rand=ConstantJitter(0.5))
    assert backoff.delay_for(1) == 3.0


def test_attempt_numbers_start_at_one():
    backoff = Backoff()
    with pytest.raises(ValueError):
        backoff.delay_for(0)


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError):
        Backoff(base=-1)
    with pytest.raises(ValueError):
        Backoff(factor=0.5)
    with pytest.raises(ValueError):
        Backoff(base=5, cap=1)
    with pytest.raises(ValueError):
        Backoff(jitter=1.5)


def test_no_backoff_never_waits():
    assert NO_BACKOFF.series(3) == [0.0, 0.0, 0.0]


def test_describe():
    assert "base 1s" in Backoff(base=1.0).describe()
