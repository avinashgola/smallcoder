"""Wiring: build the demo application with its usual middleware stack."""

from middleware.builtins import ErrorEnvelope, RequestId, RequireJson, SecurityHeaders
from web.application import Application

from . import api, pages
from .store import SEED, TaskStore


def create_app(seed=SEED, **settings):
    """Build the application the way the service starts it in production."""
    app = Application(**settings)
    app.use(RequestId())
    app.use(SecurityHeaders())
    app.use(ErrorEnvelope())
    app.use(RequireJson())
    store = TaskStore(seed)
    api.register(app, store)
    pages.register(app, store)
    app.store = store
    return app
