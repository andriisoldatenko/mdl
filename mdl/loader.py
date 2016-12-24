import yaml

from . import exceptions
from .compat import string_types

__all__ = ('Loader',)


class Loader(object):

    def __init__(self):
        self._apps = {}
        self._packages = set()

    def configure(self, config):
        # type: (Configurator) -> None
        pass

    def load(self, s, flavor=None, name=None):
        return self._process(yaml.load(s), flavor, name)

    def packages(self):
        return self._packages

    def commit(self, config):
        for app in self._apps.values():
            self.create_app(app, config)

            for route in app.routes:
                self.create_route(app, route, config)

    def create_app(self, app, config):
        raise NotImplementedError  # pragma: no cover

    def create_route(self, app, route, config):
        raise NotImplementedError  # pragma: no cover

    def _process(self, data, flavor, name):
        if flavor is not None:
            fv = data.get('flavor')
            if fv is not None and flavor != fv:
                print('Flavor does not match %s<>%s skip: %s' % (
                    flavor, fv, name))
                return

        # type: (Dict) -> None
        for key, value in data.items():
            if key in ('flavor',):
                continue

            if key == 'package':
                if isinstance(value, string_types):
                    value = (value,)

                self._packages.update(value)

            elif key == 'application':
                if 'name' not in value:
                    raise exceptions.ApplicationNameRequired()

                name = value['name']
                app = self._apps.get(name)
                if app is None:
                    app = self._apps[name] = Application(name)

                app.process(value)
            else:
                raise exceptions.UnknownFieldError(key, value)

        return self


class Application:

    def __init__(self, name):
        self.name = name
        self.itransform = None
        self.otransform = None
        self.errors = {}
        self.routes = []
        self.params = {}

    def get_params(self):
        params = dict(self.params)
        params['itransform'] = self.itransform
        params['otransform'] = self.otransform
        params['errors'] = self.errors
        return params

    def process(self, data):
        for key, value in data.items():
            f = getattr(self, '%s_' % key, None)
            if f is None:
                if key in self.params:
                    if not isinstance(self.params[key], list):
                        raise exceptions.UnknownFieldError(key, value)
                    self.params[key].append(value)

                self.params[key] = value
            else:
                f(value)

    def name_(self, data):
        if self.name is not None and self.name != data:
            raise exceptions.ApplicationNameIsRequired()

        self.name = data

    def itransform_(self, data):
        if self.itransform is not None:
            raise exceptions.AttributeIsDefined('itransform', data)

        if isinstance(data, string_types):
            data = (data,)

        self.itransform = tuple(data)

    def otransform_(self, data):
        if self.otransform is not None:
            raise exceptions.AttributeIsDefined('otransform', data)

        if isinstance(data, string_types):
            data = (data,)

        self.otransform = tuple(data)

    def errors_(self, data):
        if isinstance(data, dict):
            data = [data]
        for item in data:
            self.errors.update(item)

    def routes_(self, data):
        for route_info in data:
            if 'name' not in route_info:
                raise exceptions.NameIsRequired(data)

            name = route_info['name']

            route = None
            for _route in self.routes:
                if _route.name == name:
                    route = _route
                    break

            if route is None:
                route = Route(name)
                self.routes.append(route)

            route.process(route_info)


class Route(object):

    def __init__(self, name):
        self.name = name
        self.path = None
        self.transform = None
        self.iface = None
        self.methods = set()
        self.errors = {}
        self.params = {}

    def get_params(self):
        params = dict(self.params)
        params['errors'] = self.errors
        return params

    def process(self, data):
        for key, value in data.items():
            f = getattr(self, '%s_' % key, None)
            if f is None:
                if key in self.params:
                    if not isinstance(self.params[key], list):
                        raise exceptions.UnknownFieldError(key, value)
                    self.params[key].append(value)

                self.params[key] = value
            else:
                f(value)

    def name_(self, data):
        if self.name is not None and self.name != data:
            raise exceptions.NameIsRequired(self)

        self.name = data

    def path_(self, data):
        if self.path is not None and self.path != data:
            raise exceptions.PathIsRequired()

        self.path = data

    def transform_(self, data):
        if self.transform is not None:
            raise exceptions.AttributeIsDefined()

        self.transform = tuple(data)

    def errors_(self, data):
        if isinstance(data, dict):
            data = [data]
        for item in data:
            self.errors.update(item)
