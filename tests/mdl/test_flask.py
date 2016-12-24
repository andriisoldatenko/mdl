import json
import unittest
try:
    from unittest import mock
except ImportError:
    import mock

import mdl
from mdl import interfaces


blueprint = mock.Mock()


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
package: tests.mdl.test_flask

application:
  name: TestApp
  blueprint: tests.mdl.test_flask.blueprint

  itransform:
    - tests.mdl.test_flask.from_json

  otransform:
    - tests.mdl.test_flask.to_json

  routes:
    - path: /some-path
      name: testing
      methods: "POST"
      transform:
         - tests.mdl.test_flask.error
      errors:
         - tests.mdl.test_flask.TestException: tests.mdl.test_flask.error_json

    - path: /testing2
      name: testing2
      methods: "POST"
      transform:
         - tests.mdl.test_flask.resp

    - path: /testing3
      name: testing3
      methods: "POST"
      transform:
         - tests.mdl.test_flask.TR1

"""

BP = mdl.FlaskBlueprint(
    'TestApp2',
    'tests.mdl.test_flask.blueprint',
    itransform=['tests.mdl.test_flask.from_json'],
    otransform=to_json)

BP.add_route(
    'testing', '/confirm',
    ['tests.mdl.test_flask.error'], **{'methods': ('POST',)})


class ApplicationTestCase(unittest.TestCase):

    def setUp(self):
        blueprint.reset()

    def test_app(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.FlaskLoader(), registry)
        config.loader.load(DATA)
        config.scan('tests.mdl.test_flask')
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        self.assertEqual(app.name, 'TestApp')
        self.assertIs(app.blueprint, blueprint)
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
        self.assertIs(app2.blueprint, blueprint)
        self.assertIs(app2.registry, registry)
        self.assertIsNotNone(app2['testing'])

    def test_exc_handling(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.FlaskLoader(), registry)
        config.loader.load(DATA)
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        route = app['testing']

        res = route('{"test": "data"}')
        self.assertEqual(res, '{"error": "TestException"}')

    def test_route(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.FlaskLoader(), registry)
        config.loader.load(DATA)
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        route = app['testing2']

        res = route('{"test": "data"}')
        self.assertEqual(res, '{"test": "xxx"}')

    def test_route_transform(self):
        registry = mdl.Registry()

        config = mdl.Configurator(mdl.FlaskLoader(), registry)
        config.loader.load(DATA)
        config.commit()

        app = registry.getUtility(interfaces.IApplication, 'TestApp')
        route = app['testing3']

        res = route('{"test": "data"}')
        self.assertEqual(res, '{"test": "xxx"}')
