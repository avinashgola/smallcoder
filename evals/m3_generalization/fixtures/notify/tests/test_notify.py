from messaging.email.format import render_email
from messaging.sms.format import SMS_LIMIT, render_sms


def test_short_sms_untouched():
    assert render_sms("ops", "disk usage at 80%") == "ops: disk usage at 80%"


def test_long_sms_fits_within_limit():
    text = render_sms("alerts", "x" * 300)
    assert text.endswith("...")
    assert len(text) <= SMS_LIMIT


def test_truncated_sms_uses_the_full_budget():
    assert len(render_sms("alerts", "y" * 300)) == SMS_LIMIT


def test_email_subject_untouched_when_short():
    msg = render_email("ops", "nightly report", "all green")
    assert "Subject: nightly report" in msg


def test_email_body_preserved():
    msg = render_email("ops", "s", "line one\nline two")
    assert msg.endswith("line one\nline two")
