import sys

from . import interfaces
from .declarations import implements, directlyProvides

__all__ = ('Context',)


class Context(object):
    implements(interfaces.IContext)

    def __init__(self, markers=()):
        self._contexts = {}
        self._stack = [ContextItem()]

        if markers:
            directlyProvides(self, markers)

    def __del__(self):
        if len(self._stack) > 1:
            # something is wrong
            pass

        self._stack[0]._teardown()

    def __enter__(self):
        item = ContextItem()
        self._stack.append(item)
        return item

    def __exit__(self, exc_type, exc_value, exc_tb):
        item = self._stack.pop()
        item._teardown()

        if len(self._stack) == 1:
            self._stack[0]._teardown()

        return False

    def teardown(self):
        if len(self._stack) > 1:
            # something is wrong
            pass

        self._stack[0]._teardown()

    def register_teardown_callback(self, callback):
        """Register callable to be called when context exits"""
        self._stack[-1].register_teardown_callback(callback)


class ContextItem(object):

    def __init__(self):
        self._teardown_callbacks = []

    def _teardown(self, exc=None):
        callbacks = self._teardown_callbacks
        self._teardown_callbacks = []

        if exc is None:
            exc = sys.exc_info()[1]

        for func in reversed(callbacks):
            func(exc)

    def register_teardown_callback(self, callback):
        self._teardown_callbacks.append(callback)


class Params(object):

    def __init__(self, **params):
        self.__dict__.update(params)

    @staticmethod
    def generate_class(op):
        """ Generate class for swagger operation """
        slots = {'__oper__'}
        attrs = {'__oper__': op}

        for name, element in op.params.items():
            slots.add(name)
            attrs[name] = ParamsProperty(name)

        name = 'Params_%s' % op.operation_id
        cls = type(name, (Params,), attrs)
        cls.__slots__ = tuple(slots)

        return cls


class ParamsProperty(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, ob, type):
        try:
            return ob.__dict__[self.name]
        except KeyError:
            raise AttributeError

    def __set__(self, ob, val):
        raise AttributeError
