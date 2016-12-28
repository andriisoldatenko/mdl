from __future__ import absolute_import

import asyncio
try:
    from aiohttp import hdrs
    has_aiohttp = True
except ImportError:  # pragma: no cover
    has_aiohttp = False

from .. import interfaces
from ..context import Params
from ..declarations import implements
from ..exceptions import ConfigurationError
from ..loader import Loader
from ..runtime import Error, Errors
from ..runtime import Route as _Route, Application as _Application

from .interfaces import IRoute
from .web import WebApplication

__all__ = ('Loader', 'Application', 'init_applications')


def init_applications(registry, root=None, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    if root is None:
        for name, app in registry.getUtilitiesFor(interfaces.IApplication):
            if not app.base_path:
                root = app.init_runtime(loop=loop)
                break
        else:
            root = WebApplication(loop=loop)

    for name, app in registry.getUtilitiesFor(interfaces.IApplication):
        if app.base_path:
            app.init_runtime(root)

    return root


class Loader(Loader):

    def configure(self, config, swagger_config):
        super(Loader, self).configure(config, swagger_config)

        if not has_aiohttp:
            raise ConfigurationError('aiohttp is not available')

    def create_app(self, spec, app_info, config):
        app = Application(
            app_info.name, app_info.base_path,
            app_info.in_transform, app_info.out_transform, app_info.errors)

        def register():
            app.register(config)

        config.action(app.discriminator, register, Application.ORDER)

    def create_operation(self, op, app_info, op_info, config):
        route = RouteConfig(
            op, app_info.name, op_info.id, op_info.path,
            op_info.transform, op_info.errors, op_info.method)

        def register():
            route.register(config)

        config.action(route.discriminator, register, RouteConfig.ORDER)


class Route(_Route):
    implements(IRoute)

    _is_coroutine = True

    def __init__(self, *args, **kwargs):
        super(Route, self).__init__(*args, **kwargs)

        self.op = self.options.pop('op')
        self.params_cls = Params.generate_class(self.op)

    async def __call__(self, request):
        return (await self.transform(request))


class RuntimeApplication(_Application):

    def __init__(self, registry, name, base_path,
                 itransform, otransform, errors, **options):
        super(RuntimeApplication, self).__init__(registry, name, **options)

        self.name = name
        self.base_path = base_path
        self.in_transform = itransform
        self.out_transform = otransform
        self.errors = errors

    def init_runtime(self, root=None, loop=None):
        app = WebApplication(loop=loop)

        for route in self.routes():
            method = route.get_option('method', hdrs.METH_ANY)
            app.router.add_route(method, route.path, route)

        if root is not None:
            root.add_subapp(app.base_path, app)

        return app


class Application:

    ORDER = 100

    def __init__(self, name, base_path,
                 itransform=None, otransform=None, errors=None):
        self.name = name
        self.base_path = base_path
        self.itransform = itransform if itransform is not None else ()
        self.otransform = otransform if otransform is not None else ()
        self.errors = errors if errors is not None else {}
        self._routes = []

    @property
    def discriminator(self):
        return ('AiohttpApplicationConfigurator', self.name)

    def register(self, config):
        itransform = config.maybe_dotted_seq(self.itransform)
        otransform = config.maybe_dotted_seq(self.otransform)

        errors = []
        for exc, handler in self.errors.items():
            exc = config.maybe_dotted(exc)
            handler = config.maybe_dotted(handler)
            errors.append(Error(exc, handler))

        app = RuntimeApplication(
            config.registry,
            self.name, self.base_path, itransform, otransform, Errors(errors))

        config.registry.registerUtility(
            app, interfaces.IApplication, name=self.name)


class RouteConfig(object):

    ORDER = 1000

    def __init__(self, op, app, name, path, transform,
                 errors=None, method=hdrs.METH_ANY, **options):
        self.op = op
        self.app = app
        self.name = name
        self.path = path
        self.transform = transform
        self.errors = errors if errors is not None else {}
        self.options = options
        self.options['method'] = method

    @property
    def discriminator(self):
        return ('AiohttpApplicationRouteConfigurator', self.app, self.name)

    def register(self, config):
        errors = []
        for exc, handler in self.errors.items():
            exc = config.maybe_dotted(exc)
            handler = config.maybe_dotted(handler)
            errors.append(Error(exc, handler))

        transforms = []
        for f in self.transform:
            f = config.maybe_dotted(f)
            transforms.append(f)

        # parent application
        app = config.registry.getUtility(
            interfaces.IApplication, name=self.app)

        # transformatino for route
        # route_transform = Transform(
        #    config.maybe_dotted_seq(self.transform), Errors(errors))

        # complete transformation
        # transform = Transform(
        #    app.in_transform +
        #    (route_transform,) + app.out_transform, app.errors)

        # route registration
        route = Route(
            config.registry, self.name, self.path,
            transforms[0], op=self.op, **self.options)
        app.register_route(route)
