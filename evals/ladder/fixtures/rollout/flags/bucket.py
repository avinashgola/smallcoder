"""Stable assignment of subjects to rollout buckets."""

import zlib

BUCKETS = 100


def clamp(percent):
    """Keep a rollout percentage inside 0..100."""
    return max(0, min(BUCKETS, int(percent)))


def bucket_of(flag, subject):
    """The bucket, 0 to 99, that a subject falls into for one flag.

    Salting the key with the flag name keeps flags independent of each other:
    being early in one rollout says nothing about the next one.
    """
    key = f"{flag}:{subject}".encode("utf-8")
    return zlib.crc32(key) % BUCKETS


def in_rollout(flag, subject, percent):
    """True when the subject's bucket is part of the rolled-out share.

    A rollout of ``percent`` covers that many of the hundred buckets, so 0
    covers nobody at all and 100 covers everybody.
    """
    return bucket_of(flag, subject) <= clamp(percent)


def share(flag, subjects, percent):
    """How many of ``subjects`` a rollout of ``percent`` covers."""
    return sum(1 for subject in subjects if in_rollout(flag, subject, percent))
