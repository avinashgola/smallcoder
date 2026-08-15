"""Letter grades and pass/fail summaries for a course."""

THRESHOLDS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]


def letter_grade(score):
    """Map a numeric score (0-100) to a letter grade."""
    if not 0 <= score <= 100:
        raise ValueError(f"score out of range: {score}")
    for cutoff, letter in THRESHOLDS:
        if score > cutoff:
            return letter
    return "F"


def passing(scores):
    """Return the scores that earned a passing grade, in input order."""
    return [score for score in scores if letter_grade(score) != "F"]


def summary(scores):
    """Count how many scores earned each letter grade."""
    counts = {}
    for score in scores:
        grade = letter_grade(score)
        counts[grade] = counts.get(grade, 0) + 1
    return counts
