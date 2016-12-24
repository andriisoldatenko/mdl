__version__ = '0.1a0'

from .interface import *  # noqa
from .declarations import *  # noqa
from .config import Configurator  # noqa
from .context import *  # noqa
from .decorators import *  # noqa
from .loader import *  # noqa
from .registry import *  # noqa
from .runtime import *  # noqa
from .interfaces import IContext, ANY  # noqa
from .scripts import bootstrap  # noqa
from .verify import *  # noqa


__all__ = (decorators.__all__ +  # noqa
           declarations.__all__ +  # noqa
           context.__all__ +  # noqa
           loader.__all__ +  # noqa
           interface.__all__ +  # noqa
           registry.__all__ +  # noqa
           runtime.__all__ +  # noqa
           verify.__all__  # noqa
) + ('ANY', 'IContext', 'bootstrap', 'Configurator')


try:
    from ._flask import *  # noqa
    __all__ = __all__ + _flask.__all__  # noqa
except ImportError:  # pragma: no cover
    pass
