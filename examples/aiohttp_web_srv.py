#!/usr/bin/env python3
"""Example for aiohttp.web basic server"""

import mdl
import asyncio
import textwrap

from aiohttp.web import Application, Response, StreamResponse, run_app


class ItemID(object):

    def __init__(self, value):
        self.value = value


@mdl.format('itemID')
class ItemIDFormat(mdl.SwaggerFormat):

    def to_wire(self, item):
        return item.value

    def to_python(self, value):
        return ItemID(value)


async def index(ctx):
    return textwrap.dedent(
    """
    Type {url}/hello/John  {url}/simple or {url}/{item_id}/ in browser url bar

    """).format(url='127.0.0.1:8080', item_id='12345')


async def item_info(ctx):
    return b"Body changed %s\n\n" % str(ctx.params.item_id).encode('utf-8')


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
