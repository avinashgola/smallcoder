from flags.bucket import bucket_of, clamp, in_rollout, share

USERS = [f"user-{n}" for n in range(1, 201)]


def test_the_same_inputs_always_give_the_same_bucket():
    assert bucket_of("dark_mode", "user-1") == 64
    assert bucket_of("dark_mode", "user-1") == bucket_of("dark_mode", "user-1")


def test_flags_bucket_independently_of_each_other():
    assert bucket_of("dark_mode", "user-1") != bucket_of("new_editor", "user-1")


def test_every_bucket_is_in_range():
    assert all(0 <= bucket_of("dark_mode", user) < 100 for user in USERS)


def test_a_rollout_of_zero_covers_nobody():
    assert share("holiday_theme", USERS, 0) == 0


def test_a_rollout_of_one_hundred_covers_everybody():
    assert share("dark_mode", USERS, 100) == len(USERS)


def test_the_boundary_bucket_sits_outside_the_rollout():
    assert bucket_of("dark_mode", "user-96") == 50
    assert in_rollout("dark_mode", "user-96", 50) is False
    assert in_rollout("dark_mode", "user-96", 51) is True


def test_a_growing_rollout_never_drops_anyone():
    covered = [share("dark_mode", USERS, percent) for percent in range(0, 101, 10)]
    assert covered == sorted(covered)


def test_percentages_outside_the_range_are_clamped():
    assert clamp(-5) == 0
    assert clamp(140) == 100
    assert clamp(30) == 30
