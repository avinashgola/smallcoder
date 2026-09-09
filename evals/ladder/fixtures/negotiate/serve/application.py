"""The application object."""

from content.renderers import renderer_for
from content.types import JSON, with_charset
from wire.etag import etag_for, tag_matches
from wire.response import Response
from wire.status import NOT_MODIFIED, OK

from .config import Settings
from .errors import HttpError
from .router import Router


class Server:
    """Routes requests to resources and renders the errors they raise."""

    def __init__(self, settings=None, **overrides):
        if isinstance(settings, Settings):
            self.settings = settings
        else:
            merged = dict(settings or {})
            merged.update(overrides)
            self.settings = Settings(**merged)
        self.router = Router()

    def add(self, template, handler, methods=("GET",), name=None):
        return self.router.add(template, handler, methods, name)

    def resource(self, template, resource, name=None):
        """Mount a resource object, which brings its own method list."""
        entry = self.router.add(template, resource.dispatch, resource.methods,
                                name or type(resource).__name__)
        resource.settings = self.settings
        return entry

    def handle(self, request):
        try:
            entry, captured = self.router.resolve(request.method, request.path)
            request.vars = captured
            request.notes["route"] = entry.name
            result = entry.handler(request)
            response = result if isinstance(result, Response) else self.render(result)
        except HttpError as error:
            response = self.render_error(error)
        return self.conditional(request, response).close()

    def conditional(self, request, response):
        """Tag successful reads and answer 304 when the client is current."""
        if response.status != OK or request.method not in ("GET", "HEAD"):
            return response
        tag = etag_for(response.body)
        response.headers.default("ETag", tag)
        if tag_matches(tag, request.headers.first("If-None-Match")):
            response.status = NOT_MODIFIED
            response.body = b""
        return response

    def render(self, data):
        """Render a plain value the way the JSON endpoints expect."""
        renderer = renderer_for(JSON)
        charset = self.settings.charset
        return Response(renderer.encode(data, charset), OK,
                        content_type=with_charset(JSON, charset))

    def render_error(self, error):
        response = self.render(error.body())
        response.status = error.status
        for name, value in error.headers.items():
            response.headers.put(name, value)
        return response

    def __repr__(self):
        return "<Server %d routes>" % len(self.router)
