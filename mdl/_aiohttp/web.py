""" Custom application object """
from aiohttp import hdrs, web

from .interfaces import IRoute
from .params import unmarshal_request
from ..context import Context


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
            resp = (
                await match_info.expect_handler(request))

        if resp is None:
            handler = match_info.handler

            # init operations params
            if IRoute.providedBy(handler):
                ctx = Context(
                    request,
                    unmarshal_request(handler.params_cls, request))
            else:
                ctx = request

            for app in match_info.apps:
                for factory in reversed(app.middlewares):
                    handler = await factory(app, handler)
            resp = await handler(ctx)

        assert isinstance(resp, web.StreamResponse), (
            "Handler {!r} should return response instance, "
            "got {!r} [middlewares {!r}]").format(
                match_info.handler, type(resp),
                [mw for mw in app.middlewares for app in match_info.apps])

        return resp
