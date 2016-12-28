from .. import interface
from ..interfaces import IContext


class IRequest(interface.Interface):
    """ web request """


class IResponse(interface.Interface):
    """ response """


class IParameters(interface.Interface):
    """ parameters """
    

class IWebContext(IContext):
    """Web handler context"""

    params = interface.Attribute('Parameters', spec='IParameters')

    request = interface.Attribute('Request', spec='IRequest')
    response = interface.Attribute('Response', spec='IResponse')
