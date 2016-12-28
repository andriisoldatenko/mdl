""" Response renderer """
from aiohttp.protocol import HttpVersion10, HttpVersion11
from aiohttp.protocol import WebResponse as ResponseImpl

from ..web import hdrs
from ..web.response import ContentCoding


class ResponseRenderer(object):

    def __init__(self, ctx, response):
        self.ctx = ctx
        self.request = None
        self.response = response

        self.eof_sent = False
        self.resp_impl = None
        self.keep_alive = None

    @property
    def status(self):
        return self.ctx.response.status

    @property
    def body_length(self):
        return self.resp_impl.body_length

    @property
    def output_length(self):
        return self.resp_impl.output_length

    def prepare(self, request,
               HttpVersion10=HttpVersion10,
               HttpVersion11=HttpVersion11,
               CONNECTION=hdrs.CONNECTION,
               DATE=hdrs.DATE,
               SERVER=hdrs.SERVER,
               SET_COOKIE=hdrs.SET_COOKIE,
               TRANSFER_ENCODING=hdrs.TRANSFER_ENCODING):

        yield from request._prepare_hook(self)

        self.request = request

        # set content type
        if self.ctx.response.content_type is None:
            self.ctx.response.content_type = self.ctx.op.produces[0]

        # respone body
        if isinstance(self.response, str):
            charset = self.ctx.response.charset
            if charset is None:
                charset = 'utf-8'
                self.ctx.response.charset = charset

            body = self.response.encode(charset)
        else:
            body = self.response

        # keep-alive
        keep_alive = self.ctx.keep_alive
        if keep_alive is None:
            keep_alive = request.keep_alive
        self.keep_alive = keep_alive

        version = request.version

        resp_impl = self.resp_impl = ResponseImpl(
            request._writer,
            self.ctx.response.status,
            version,
            not keep_alive,
            self.ctx.response.reason)

        headers = self.ctx.response.headers
        #for cookie in self.ctx.response.cookies.values():
        #    value = cookie.output(header='')[1:]
        #    headers.add(SET_COOKIE, value)

        if self.ctx.response.content_coding is not None:
            self._start_compression(request)

        if self.ctx.response.chunked:
            if request.version != HttpVersion11:
                raise RuntimeError(
                    "Using chunked encoding is forbidden "
                    "for HTTP/{0.major}.{0.minor}".format(request.version))
            resp_impl.chunked = True
            if self.ctx.response.chunk_size:
                resp_impl.add_chunking_filter(self.ctx.response.chunk_size)
            headers[TRANSFER_ENCODING] = 'chunked'
        else:
            content_length = self.ctx.response.content_length
            if content_length is None:
                self.ctx.response.content_length = len(body)

            resp_impl.length = self.ctx.response.content_length

        headers.setdefault(DATE, request.time_service.strtime())
        headers.setdefault(SERVER, resp_impl.SERVER_SOFTWARE)
        if CONNECTION not in headers:
            if keep_alive:
                if version == HttpVersion10:
                    headers[CONNECTION] = 'keep-alive'
            else:
                if version == HttpVersion11:
                    headers[CONNECTION] = 'close'

        resp_impl.headers = headers
        resp_impl.send_headers()

        yield from self.write(body)

    def _do_start_compression(self, coding):
        if coding != ContentCoding.identity:
            self.ctx.response.headers[hdrs.CONTENT_ENCODING] = coding.value
            self.ctx.response.content_length = None
            self.resp_impl.add_compression_filter(coding.value)

    def _start_compression(self, request):
        if self.ctx.response.content_coding is not None:
            self._do_start_compression(self.ctx.response.content_coding)
        else:
            accept_encoding = request.headers.get(hdrs.ACCEPT_ENCODING, '').lower()
            for coding in ContentCoding:
                if coding.value in accept_encoding:
                    self._do_start_compression(coding)
                    return

    def write(self, data):
        assert isinstance(data, (bytes, bytearray, memoryview)), \
            "data argument must be byte-ish (%r)" % type(data)

        if self.eof_sent:
            raise RuntimeError("Cannot call write() after write_eof()")
        if self.resp_impl is None:
            raise RuntimeError("Cannot call write() before start()")

        if data:
            return self.resp_impl.write(data)
        else:
            return ()

    def drain(self):
        if self.resp_impl is None:
            raise RuntimeError("Response has not been started")
        yield from self.resp_impl.transport.drain()

    def write_eof(self):
        if self.eof_sent:
            return
        if self.resp_impl is None:
            raise RuntimeError("Response has not been started")

        yield from self.resp_impl.write_eof()
        self.eof_sent = True
