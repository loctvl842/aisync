"""
Utility functions for AISync
"""

from aisync.utils.json import dict_deep_extend
from aisync.utils.pattern import memoize, singleton

__all__ = [
    "dict_deep_extend",
    "memoize",
    "singleton",
]
