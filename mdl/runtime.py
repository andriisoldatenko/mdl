from .context import Context
from .declarations import implements
from .interfaces import IApplication

__all__ = ('Transform', 'Error', 'Errors', 'Route')


class Transform(object):
    # implements(ITransform)

    def __init__(self, transforms, errors):
        self._transforms = transforms
        self._errors = errors

    def __call__(self, ctx, model):
        try:
            for transform in self._transforms:
                model = transform(ctx, model)
        except self._errors.exceptions as exc:
            model = self._errors.process(ctx, exc)

        return model


class Error(object):

    def __init__(self, exc, handler):
        self.exc = exc
        self.handler = handler


class Errors(object):
    # very simple exception handling code;
    # we can use zope.interface adaptation or code generation to make it faster

    def __init__(self, errors):
        self.errors = errors
        self.exceptions = tuple(err.exc for err in errors)

    def process(self, ctx, exc):
        for err in self.errors:
            if isinstance(exc, err.exc):
                return err.handler(ctx, exc)

        raise RuntimeError('Can not find exception handler')


class Route(object):

    def __init__(self, registry, name, path, transform, markers=(), **options):
        self.registry = registry
        self.name = name
        self.path = path
        self.transform = transform
        self.options = options
        self.markers = markers

    def get_option(self, name, default=None):
        return self.options.get(name, default)

    def __call__(self, model):
        return self.transform(Context(self.markers), model)


class Application(object):
    implements(IApplication)

    def __init__(self, registry, name, **options):
        self.registry = registry
        self.name = name
        self.options = options
        self._routes = {}

    def keys(self):
        return self._routes.keys()

    def items(self):
        return self._routes.items()

    def routes(self):
        return self._routes.values()

    def __getitem__(self, key):
        return self._routes[key]

    def register_route(self, route):
        self._routes[route.name] = route
