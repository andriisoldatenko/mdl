import venusian
from zope.interface.interfaces import IInterface

from .compat import string_types
from .declarations import implements, directlyProvides
from .exceptions import ConfigurationError
from .interface import Interface
from .interfaces import ANY, CATEGORY
from .interfaces import ITransform, ITransformDefinition
from .verify import verifyObject

__all__ = ('transform', 'adapter', 'config')

_marker = object()


def config(ob=_marker, factory=_marker):
    flavor = None

    def register(scanner, name, wrapped):
        wrapped(scanner.config)

    def wrap(factory):
        flavor
        venusian.attach(factory, register, category=CATEGORY)
        return factory

    if ob is _marker and factory is _marker:
        flavor = None
    elif ob is not _marker and factory is not _marker:
        flavor = ob
        venusian.attach(factory, register, category=CATEGORY)
        return factory
    elif callable(ob) and factory is _marker:
        flavor = None
        venusian.attach(ob, register, category=CATEGORY)
        return ob
    elif isinstance(ob, string_types) and factory is _marker:
        flavor = ob
    else:
        raise ConfigurationError('unknowncan not process config decorator')

    return wrap


class adapter(object):

    def __init__(self, required, provided=None, name=u''):
        if IInterface.providedBy(required):
            required = (required,)

        self.name = name
        self.required = required
        self.provided = provided

    def register(self, scanner, name, wrapped):
        scanner.config.add_adapter(
            wrapped, required=self.required,
            provided=self.provided, name=self.name)

    def __call__(self, factory):
        venusian.attach(factory, self.register, category=CATEGORY)
        return factory


class _ITransformFunction(Interface):
    """ marker interface for transform function """


class transform(object):
    implements(ITransformDefinition)

    def __init__(self, in_model, out_model, name=None, description=None):
        self.name = name
        self.description = description
        self.in_model = in_model
        self.out_model = out_model

    def _register(self, scanner, name, wrapped):
        resolver = scanner.config.resolver
        if self.in_model != ANY:
            self.in_model = resolver.maybe_resolve(self.in_model)
        if self.out_model != ANY:
            self.out_model = resolver.maybe_resolve(self.out_model)

    def __call__(self, f):
        verifyObject(ITransform, f, True)
        directlyProvides(f, (ITransform, _ITransformFunction))

        self.func = f
        if self.name is None:
            self.name = f.__name__
        if self.description is None:
            self.description = f.__doc__

        venusian.attach(f, self._register, category=CATEGORY)
        f.__trans_def__ = self
        return f


@adapter(_ITransformFunction, ITransformDefinition)
def get_trans_definition(transform):
    return transform.__trans_def__
