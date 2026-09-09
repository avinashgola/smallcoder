"""Packaged defaults -- the lowest priority layer.

These are the development values.  Deployments ship a profile file that turns
the noisy bits off and points the service at real hosts.
"""

DEFAULTS = {
    "server": {
        "host": "127.0.0.1",
        "port": 8080,
        "workers": 4,
    },
    "logging": {
        "level": "info",
        "debug": True,
        "file": None,
    },
    "http": {
        "retries": 3,
        "timeout": 30.0,
        "keepalive": True,
    },
    "features": {
        "beta_ui": False,
        "export_csv": True,
    },
}

REQUIRED_PATHS = (
    "server.host",
    "server.port",
    "logging.level",
    "http.retries",
)
