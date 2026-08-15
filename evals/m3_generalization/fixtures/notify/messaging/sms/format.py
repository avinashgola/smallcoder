"""Render notification text for the 160-character SMS channel."""

SMS_LIMIT = 160


def render_sms(sender, body):
    """One SMS-sized message; long bodies are truncated with an ellipsis."""
    text = f"{sender}: {body}"
    if len(text) > SMS_LIMIT:
        text = text[:SMS_LIMIT] + "..."
    return text
