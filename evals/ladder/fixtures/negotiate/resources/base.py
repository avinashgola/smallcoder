"""The resource base class: collect data, then negotiate a representation."""

from content.renderers import renderer_for
from content.selection import choose, choose_language
from content.types import CSV, HTML, JSON, TEXT
from serve.errors import NotAcceptable
from wire.headers import vary
from wire.response import Response
from wire.status import OK


class Resource:
    """A read-only resource.

    ``offers`` lists the media types this resource can produce, best first:
    the head of the list is what a client that has no preference should get.
    """

    offers = (JSON, CSV, HTML, TEXT)
    methods = ("GET",)
    languages = ("en",)

    def __init__(self, settings=None):
        self.settings = settings

    @property
    def charset(self):
        return getattr(self.settings, "charset", "utf-8")

    def collect(self, request):
        """Build the data this resource represents."""
        raise NotImplementedError

    def dispatch(self, request):
        """Render :meth:`collect` in whichever form the client asked for."""
        data = self.collect(request)
        media_type = choose(self.offers, request.accept())
        if media_type is None:
            raise NotAcceptable(self.offers)
        renderer = renderer_for(media_type)
        response = Response(renderer.encode(data, self.charset), OK,
                            content_type=renderer.content_type(self.charset))
        language = choose_language(self.languages,
                                   request.headers.first("Accept-Language"))
        if language is not None:
            response.headers.put("Content-Language", language)
        vary(response.headers, "Accept", "Accept-Language")
        return response

    def __repr__(self):
        return "<%s offers=%s>" % (type(self).__name__, ",".join(self.offers))
