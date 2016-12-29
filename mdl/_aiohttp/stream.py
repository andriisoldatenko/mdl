""" Response stream """


class Stream(object):

    def __init__(self):
        self._resp = None
        self._eof_sent = False

    def start(self, response):
        self._resp = response

    def write(self, data):
        assert isinstance(data, (bytes, bytearray, memoryview)), \
            "data argument must be byte-ish (%r)" % type(data)

        if self._eof_sent:
            raise RuntimeError("Cannot call write() after write_eof()")
        if self._resp is None:
            raise RuntimeError("Cannot call write() before start()")

        if data:
            return self._resp.write(data)
        else:
            return ()

    def drain(self):
        if self._resp is None:
            raise RuntimeError("Response has not been started")
        yield from self._resp.transport.drain()

    def write_eof(self):
        if self._eof_sent:
            return
        if self._resp is None:
            raise RuntimeError("Response has not been started")

        yield from self._resp.write_eof()
        self.eof_sent = True
