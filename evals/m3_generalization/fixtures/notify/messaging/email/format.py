"""Render notification text for the email channel."""

SUBJECT_LIMIT = 78


def render_email(sender, subject, body):
    """A plain-text email with a length-limited subject line."""
    if len(subject) > SUBJECT_LIMIT:
        subject = subject[: SUBJECT_LIMIT - 3] + "..."
    return f"From: {sender}\nSubject: {subject}\n\n{body}"
