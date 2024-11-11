"""
Utility functions for AISync
"""

from aisync.utils.json import dict_deep_extend
from aisync.utils.path import get_project_root, get_suit_name, get_suits_base_path
from aisync.utils.pattern import memoize, singleton

__all__ = [
    "dict_deep_extend",
    "get_project_root",
    "get_suit_name",
    "get_suits_base_path",
    "memoize",
    "singleton",
]
