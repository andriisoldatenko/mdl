from zope import interface

ANY = '*'
UNKNOW = object()
CATEGORY = 'mdl'


class IApplication(interface.Interface):
    """Application"""


class IContext(interface.Interface):
    """Transformation context"""


class ITransform(interface.Interface):
    """Transformation"""

    def __call__(ctx, model):
        """Transform input model"""


class ITransformDefinition(interface.Interface):
    """Transform definition"""

    name = interface.Attribute(
        'name', 'Transformation name')

    description = interface.Attribute(
        'description', 'Transformation description')

    in_model = interface.Attribute(
        'in_model', 'Transformation input model')

    out_model = interface.Attribute(
        'out_model', 'Transformation output model')

    func = interface.Attribute(
        'func', 'Transformation function')


class IInspectable(interface.Interface):
    """Inspectable transformation"""

    def validate():
        """validate transformation inout/output"""

    def transforms():
        """list transforms objects"""
