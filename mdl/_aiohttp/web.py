""" Custom application object """
from aiohttp import hdrs, web

from ..web.context import WebContext

from .interfaces import IRoute
from .params import unmarshal_request
from .response import ResponseRenderer


class WebApplication(web.Application):

    async def _handle(self, request):
        match_info = await self._router.resolve(request)
        assert isinstance(match_info, web.AbstractMatchInfo), match_info
        match_info.add_app(self)
        match_info.freeze()

        resp = None
        request._match_info = match_info
        expect = request.headers.get(hdrs.EXPECT)
        if expect:
            resp = await match_info.expect_handler(request)

        if resp is None:
            handler = match_info.handler

            # init context
            if IRoute.providedBy(handler):
                ctx = WebContext(
                    handler.op, request,
                    unmarshal_request(handler.params_cls, request),
                    keep_alive=request.keep_alive)
            else:
                ctx = WebContext(
                    None, request, None,
                    keep_alive=request.keep_alive)

            for app in match_info.apps:
                for factory in reversed(app.middlewares):
                    handler = await factory(app, handler)

            body = await handler(ctx)
            return ResponseRenderer(ctx, body)

        assert isinstance(resp, web.StreamResponse), (
            "Handler {!r} should return response instance, "
            "got {!r} [middlewares {!r}]").format(
                match_info.handler, type(resp),
                [mw for mw in app.middlewares for app in match_info.apps])

        return resp
