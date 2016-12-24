"""Runtime inspectables"""
from . import adapter
from .declarations import implements
from .runtime import Transform
from .interfaces import IInspectable, ITransformDefinition


@adapter(Transform, IInspectable)
class InspecatbleTransform:
    implements(IInspectable)

    def __init__(self, transform):
        self.transform = transform
        self.definition = ITransformDefinition(transform, None)

    def transforms(self):
        return self.transform._transforms
