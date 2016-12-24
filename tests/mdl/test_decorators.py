import unittest
from zope import interface
from zope.interface.exceptions import BrokenMethodImplementation

import mdl
from mdl import interfaces


class Marker(object):

    def __init__(self, provides):
        interface.directlyProvides(self, provides)


class IMarker1(interface.Interface):
    pass


class IMarker2(interface.Interface):
    pass


def node_func(ctx, model):
    pass


def marker_adapter(marker):
    return Marker(IMarker2)


@mdl.config
def configurator(config):
    config.CONFIGURATOR_RUN = 1


class DecoratorsTestCase(unittest.TestCase):

    def setUp(self):
        self.registry = mdl.Registry()
        self.registry.install()

        self.addCleanup(self.registry.uninstall)

    def test_node(self):
        transform = mdl.transform(mdl.ANY, mdl.ANY)
        transform(node_func)

        self.assertTrue(interfaces.ITransform.providedBy(node_func))

        config = mdl.Configurator(registry=self.registry)
        config.scan(__name__)
        config.commit()

        definition = self.registry.getAdapter(
            node_func, interfaces.ITransformDefinition)
        self.assertTrue(interfaces.ITransformDefinition.providedBy(definition))

    def test_node_broken(self):

        def node_func():
            pass

        node = mdl.transform(mdl.ANY, mdl.ANY)

        with self.assertRaises(BrokenMethodImplementation):
            node(node_func)

    def test_adapter(self):
        adapter = mdl.adapter(IMarker1, IMarker2)
        adapter(marker_adapter)

        config = mdl.Configurator(registry=self.registry)
        config.scan(__name__)
        config.commit()

        marker = Marker(IMarker1)

        m = self.registry.getAdapter(marker, IMarker2)
        self.assertTrue(IMarker2.providedBy(m))

        m = IMarker2(marker)
        self.assertTrue(IMarker2.providedBy(m))

    def test_config(self):
        config = mdl.Configurator(registry=self.registry)
        config.scan('tests.mdl.test_decorators')
        config.commit()

        self.assertTrue(hasattr(config, 'CONFIGURATOR_RUN'))
