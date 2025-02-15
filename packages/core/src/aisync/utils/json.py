from functools import reduce
from typing import Any, Mapping, TypeVar

T = TypeVar("T")


def dict_deep_extend(*dicts: dict[Any, Any]) -> dict[Any, Any]:
    """
    Deeply merge multiple dictionaries.
    Later dictionaries take precedence over earlier ones.

    Args:
        *dicts: An arbitrary number of dictionaries to merge.

    Returns:
        A new dictionary resulting from deep merging the input dictionaries.

    Raises:
        TypeError: If any of the arguments is not a dictionary.
    """

    def merge(a: dict[Any, Any], b: dict[Any, Any]) -> dict[Any, Any]:
        """
        Recursively merge dictionary b into dictionary a.

        Args:
            a: The base dictionary.
            b: The dictionary to merge into a.

        Returns:
            The merged dictionary.
        """
        for key, b_value in b.items():
            if key in a:
                a_value = a[key]
                if isinstance(a_value, Mapping) and isinstance(b_value, Mapping):
                    a[key] = merge(a_value.copy(), b_value)
                else:
                    a[key] = b_value
            else:
                a[key] = b_value
        return a

    if not dicts:
        return {}

    # Validate all inputs are dictionaries
    for idx, d in enumerate(dicts, start=1):
        if not isinstance(d, Mapping):
            raise TypeError(f"Argument {idx} is not a dictionary: {d!r}")

    return reduce(merge, dicts, {})
