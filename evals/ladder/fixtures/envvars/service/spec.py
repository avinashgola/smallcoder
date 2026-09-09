"""Every environment variable the report service reads."""

from envcfg.spec import Field, Spec

LOG_LEVELS = ("debug", "info", "warning", "error")

SERVICE_SPEC = Spec(
    "APP_",
    (
        Field("database_url", required=True, secret=True),
        Field("host", default="127.0.0.1"),
        Field("port", kind="int", default=8080),
        Field("workers", kind="int", default=4),
        Field("debug", kind="bool", default=False),
        Field("log_level", default="info", choices=LOG_LEVELS),
        Field("request_timeout", kind="float", default=30.0),
        Field("allowed_origins", kind="list", default=()),
    ),
)
