"""Session bookkeeping (unrelated to permission resolution)."""

SESSION_TTL_SECONDS = 3600


class Session:
    def __init__(self, user_id, issued_at):
        self.user_id = user_id
        self.issued_at = issued_at

    def is_expired(self, now):
        return now - self.issued_at >= SESSION_TTL_SECONDS

    def remaining(self, now):
        return max(0, SESSION_TTL_SECONDS - (now - self.issued_at))
