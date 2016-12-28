""" Custom application object """
from aiohttp import hdrs, web

from .interfaces import IRoute
from .params import unmarshal_request


class WebRequest(web.Request):

    _params = None

    @property
    def params(self):
        return self._params


class WebApplication(web.Application):

    def _make_request(self, message, payload, protocol):
        return WebRequest(
            message, payload,
            protocol.transport, protocol.reader, protocol.writer,
            protocol.time_service, protocol._request_handler,
            secure_proxy_ssl_header=self._secure_proxy_ssl_header)

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
                request._params = unmarshal_request(
                    handler.params_cls, request)

            for app in match_info.apps:
                for factory in reversed(app.middlewares):
                    handler = await factory(app, handler)
            resp = await handler(request)

        assert isinstance(resp, web.StreamResponse), (
            "Handler {!r} should return response instance, "
            "got {!r} [middlewares {!r}]").format(
                match_info.handler, type(resp),
                [mw for mw in app.middlewares for app in match_info.apps])

        return resp
