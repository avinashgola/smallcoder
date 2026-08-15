from backoff import retry_schedule, total_wait


def test_default_schedule():
    assert retry_schedule() == [0.5, 1.0, 2.0]


def test_custom_base_delay():
    assert retry_schedule(4, 1) == [1, 2, 4, 8]


def test_zero_delay_means_immediate_retry():
    assert retry_schedule(3, 0) == [0, 0, 0]


def test_total_wait_with_zero_delay():
    assert total_wait(3, 0) == 0


def test_total_wait_default():
    assert total_wait() == 3.5
