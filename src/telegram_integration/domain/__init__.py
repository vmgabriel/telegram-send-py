"""Domain layer.

This package holds the pure business objects and the repository *ports*
(interfaces) that the application depends on. It must not import any
infrastructure concern such as :mod:`sqlite3`, :mod:`platformdirs` or
:mod:`requests`.
"""

from .entities import ListenerState
from .repositories import ListenerStateRepository

__all__ = ["ListenerState", "ListenerStateRepository"]
