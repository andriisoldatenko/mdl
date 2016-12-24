from __future__ import absolute_import

import venusian
try:
    from flask import request
    has_flask = True
except ImportError:  # pragma: no cover
    has_flask = False

from . import interfaces
from .compat import string_types
from .loader import Loader
from .runtime import Error, Errors, Route, Transform, Application

__all__ = ('FlaskLoader', 'FlaskBlueprint', 'FlaskBlueprintRoute')


class FlaskLoader(Loader):

    def configure(self, config):
        if has_flask:
            config.add_directive('add_blueprint', add_blueprint_directive)
            config.add_directive('add_blueprint_route', add_route_directive)

    def create_app(self, app, config):
        config.add_blueprint(app.name, **app.get_params())

    def create_route(self, app, route, config):
        config.add_blueprint_route(
            app.name, route.name, route.path,
            route.transform, **route.get_params())


class FlaskApplication(Application):

    def __init__(self, registry, name, blueprint,
                 itransform, otransform, errors, **options):
        options['blueprint'] = blueprint

        super(FlaskApplication, self).__init__(registry, name, **options)

        self.blueprint = blueprint
        self.itransform = itransform
        self.otransform = otransform
        self.errors = errors

    def register_route(self, route, path=None, **options):
        super(FlaskApplication, self).register_route(route)

        def f():
            return self(request)

        f.__name__ = route.name

        self.blueprint.add_url_rule(path, route.name, f, **options)


class FlaskBlueprint:

    ORDER = 100

    def __init__(self, name, blueprint=None,
                 itransform=None, otransform=None, errors=None, config=None):
        self.config = config
        self.name = name
        self.blueprint = blueprint
        self.itransform = itransform if itransform is not None else ()
        self.otransform = otransform if otransform is not None else ()
        self.errors = errors if errors is not None else {}
        self._routes = []

        if config is None:
            def register(scanner, name, ob):
                config = scanner.config

                def _register():
                    self.register(config)

                    for route in self._routes:
                        route.register(config)

                config.action(
                    self.discriminator, _register, FlaskBlueprint.ORDER)

            venusian.attach(self, register, category=interfaces.CATEGORY)

    @property
    def discriminator(self):
        return ('ApplicationConfigurator', self.name)

    def register(self, config):
        blueprint = config.maybe_dotted(self.blueprint)
        itransform = config.maybe_dotted_seq(self.itransform)
        otransform = config.maybe_dotted_seq(self.otransform)

        errors = []
        for exc, handler in self.errors.items():
            exc = config.maybe_dotted(exc)
            handler = config.maybe_dotted(handler)
            errors.append(Error(exc, handler))

        app = FlaskApplication(
            config.registry,
            self.name, blueprint, itransform, otransform, Errors(errors))

        config.registry.registerUtility(
            app, interfaces.IApplication, name=self.name)

    def add_route(self, name, path, transform=None, errors=None, **options):
        if self.config is not None:
            add_route_directive(
                self.config, self.name, name,
                path, transform, errors, **options)
        else:
            self._routes.append(
                FlaskBlueprintRoute(None, self.name,
                                    name, path, transform, errors, **options)
            )
        return self


class FlaskBlueprintRoute:

    ORDER = 1000

    def __init__(self, config, blueprint,
                 name, path, transform, errors=None, **options):
        self.blueprint = blueprint
        self.name = name
        self.path = path
        self.transform = transform
        self.errors = errors if errors is not None else {}
        self.options = options

    @property
    def discriminator(self):
        return ('ApplicationRouteConfigurator', self.blueprint, self.name)

    def register(self, config):
        self.options['path'] = self.path

        errors = []
        for exc, handler in self.errors.items():
            exc = config.maybe_dotted(exc)
            handler = config.maybe_dotted(handler)
            errors.append(Error(exc, handler))

        # parent application
        app = config.registry.getUtility(
            interfaces.IApplication, name=self.blueprint)

        # transformatino for route
        route_transform = Transform(
            config.maybe_dotted_seq(self.transform), Errors(errors))

        # complete transformation
        transform = Transform(
            app.itransform + (route_transform,) + app.otransform, app.errors)

        # flask route registration
        route = Route(config.registry, self.name, transform, **self.options)
        app.register_route(route, **self.options)


def add_blueprint_directive(self, name, blueprint=None,
                            itransform=None, otransform=None, errors=None):
    app = FlaskBlueprint(name, blueprint, itransform, otransform, errors, self)

    def register():
        app.register(self)

    self.action(app.discriminator, register, FlaskBlueprint.ORDER)
    return app


def add_route_directive(self, blueprint, name, path,
                        transform=None, errors=None, **options):
    if isinstance(options.get('methods'), string_types):
        options['methods'] = (options['methods'],)

    route = FlaskBlueprintRoute(
        self, blueprint, name, path, transform, errors, **options)

    def register():
        route.register(self)

    self.action(route.discriminator, register, FlaskBlueprintRoute.ORDER)
