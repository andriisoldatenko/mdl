import sys
import types

# PY3 is left as bw-compat but PY2 should be used for most checks.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:  # pragma: no cover
    string_types = basestring,  # noqa
    integer_types = (int, long)  # noqa
    class_types = (type, types.ClassType)
    text_type = unicode  # noqa
    binary_type = str
    long = long  # noqa
else:  # pragma: no cover
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
    long = int


if PY2:  # pragma: no cover
    def exec_(code, globs=None, locs=None):
        """Execute code in a namespace."""
        if globs is None:
            frame = sys._getframe(1)
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec("""exec code in globs, locs""")

    exec_("""def reraise(tp, value, tb=None):
    raise tp, value, tb
""")

else:  # pragma: no cover
    import builtins
    exec_ = getattr(builtins, "exec")

    def reraise(tp, value, tb=None):
        if value is None:
            value = tp
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    del builtins
