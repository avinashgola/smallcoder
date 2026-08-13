"""Application settings loaded from environment-style mappings."""

DEFAULTS = {"timeout": 30, "retries": 3, "debug": False}


def parse_bool(value):
    """Parse an environment-style boolean value."""
    if isinstance(value, bool):
        return value
    return bool(value)


def load_settings(env):
    """Build the settings dict from DEFAULTS plus APP_* overrides in `env`."""
    settings = dict(DEFAULTS)
    if "APP_TIMEOUT" in env:
        settings["timeout"] = int(env["APP_TIMEOUT"])
    if "APP_RETRIES" in env:
        settings["retries"] = int(env["APP_RETRIES"])
    if "APP_DEBUG" in env:
        settings["debug"] = parse_bool(env["APP_DEBUG"])
    return settings
