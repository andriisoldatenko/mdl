import json
import unittest

import mdl
from mdl import interfaces


class TestException(Exception):
    pass


@mdl.transform(mdl.ANY, mdl.ANY)
def from_json(ctx, data):
    return json.loads(data)


def to_json(ctx, data):
    return json.dumps(data)


def error(ctx, data):
    raise TestException()


def resp(ctx, data):
    return {'test': 'xxx'}


def error_json(ctx, exc):
    return {'error': 'TestException'}


TR1 = mdl.Transform([resp], mdl.Errors([]))


DATA = """
swagger: "2.0"
info:
  title: Test API
  version: "1.0.0"

basePath: /app

x-package: tests.mdl.test_aiohttp
x-name: TestApp
x-in-transform:
   - tests.mdl.test_aiohttp.from_json
x-out-transform:
   - tests.mdl.test_aiohttp.to_json

paths:
  /some-path:
    post:
       operationId: testing
       produces:
         - application/json
       responses:
         '200':
           description: OK

       x-transform:
         - tests.mdl.test_aiohttp.error
       x-errors:
         - tests.mdl.test_aiohttp.TestException:
              tests.mdl.test_aiohttp.error_json

"""


class AiohttpApplicationTestCase(unittest.TestCase):

    def test_app(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.aiohttp.Loader(), registry)
        config.loader.load(DATA)
        config.scan('tests.mdl.test_aiohttp')
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        self.assertEqual(app.name, 'TestApp')
        self.assertIs(app.registry, registry)
        self.assertIsInstance(app['testing'], mdl.Route)
        self.assertEqual(list(sorted(app.keys())),
                         sorted(['testing', 'testing2', 'testing3']))
        self.assertEqual(
            list(app.items()),
            list({'testing': app['testing'],
                  'testing2': app['testing2'],
                  'testing3': app['testing3']}.items()))
        routes = list(app.routes())
        self.assertIn(app['testing'], routes)
        self.assertIn(app['testing2'], routes)
        self.assertIn(app['testing3'], routes)

        app2 = registry.getUtility(interfaces.IApplication, 'TestApp2')
        self.assertEqual(app2.name, 'TestApp2')
        self.assertIs(app2.registry, registry)
        self.assertIsNotNone(app2['testing'])

    def _test_exc_handling(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.aiohttp.Loader(), registry)
        config.loader.load(DATA)
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        route = app['testing']

        res = route('{"test": "data"}')
        self.assertEqual(res, '{"error": "TestException"}')

    def _test_route(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.aiohttp.Loader(), registry)
        config.loader.load(DATA)
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        route = app['testing2']

        res = route('{"test": "data"}')
        self.assertEqual(res, '{"test": "xxx"}')

    def _test_route_transform(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.aiohttp.Loader(), registry)
        config.loader.load(DATA)
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        route = app['testing3']

        res = route('{"test": "data"}')
        self.assertEqual(res, '{"test": "xxx"}')
