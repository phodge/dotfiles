class Action:
    """Base class for all actions. Keeps a registry of all subclasses"""
    _registry = {}

    @classmethod
    def get_by_key(cls, key):
        return cls._registry[key]


class Touch(Action):
    key = 'touch'

    def __init__(self, *, target):
        self._target = target


for cls in (Touch, ):
    Action._registry[cls.key] = cls
