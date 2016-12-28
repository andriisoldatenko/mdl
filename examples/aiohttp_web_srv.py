#!/usr/bin/env python3
"""Example for aiohttp.web basic server"""

import mdl
import asyncio
import textwrap

from aiohttp.web import Application, Response, StreamResponse, run_app


class ItemID(object):

    def __init__(self, value):
        self.value = value


ITEM_ID_FORMAT = mdl.format(
    'itemID',
    to_wire=lambda item: item.value,
    to_python=lambda value: ItemID(value),
)


async def intro(ctx):
    txt = textwrap.dedent("""\
        Type {url}/hello/John  {url}/simple or {url}/{item_id}/
        in browser url bar
    """).format(url='127.0.0.1:8080', item_id='12345')
    binary = txt.encode('utf8')
    resp = StreamResponse()
    resp.content_length = len(binary)
    resp.content_type = 'text/plain'
    await resp.prepare(ctx.request)
    resp.write(binary)
    return resp


async def item_info(ctx):
    resp = Response()
    resp.body = b"Body changed %s" % str(ctx.params.item_id).encode('utf-8')
    resp.content_type = 'text/plain'
    return resp


def init(loop):
    config = mdl.Configurator(mdl.aiohttp.Loader)
    config.load_mdl_file('aiohttp_web_srv.mdl')
    reg = config.commit()
    reg.install()

    app = mdl.aiohttp.init_applications(reg, loop=loop)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = init(loop)
    run_app(app)
else:
    app = init(asyncio.get_event_loop())
