from functools import partial, wraps
from inspect import isbuiltin, isclass, isfunction, ismethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union


def get_callable_name(func):
    """
    Returns the best available display name for the given function/callable.

    :rtype: str

    """
    if ismethod(func):
        self = func.__self__
        cls = self if isclass(self) else type(self)
        return f"{cls.__qualname__}.{func.__name__}"
    elif isclass(func) or isfunction(func) or isbuiltin(func):
        return func.__qualname__
    elif hasattr(func, "__call__") and callable(func.__call__):
        # instance of a class with a __call__ method
        return type(func).__qualname__

    raise TypeError(f"Unable to determine a name for {func!r} -- maybe it is not a callable?")


def obj_to_ref(obj):
    """
    Returns the path to the given callable.

    :rtype: str
    :raises TypeError: if the given object is not callable
    :raises ValueError: if the given object is a :class:`~functools.partial`, lambda or a nested
        function

    """
    if isinstance(obj, partial):
        raise ValueError("Cannot create a reference to a partial()")

    name = get_callable_name(obj)
    if "<lambda>" in name:
        raise ValueError("Cannot create a reference to a lambda")
    if "<locals>" in name:
        raise ValueError("Cannot create a reference to a nested function")

    if ismethod(obj):
        module = obj.__self__.__module__
    else:
        module = obj.__module__

    return f"{module}:{name}"


def ref_to_obj(ref):
    """
    Returns the object pointed to by ``ref``.

    :type ref: str

    """
    if not isinstance(ref, str):
        raise TypeError("References must be strings")
    if ":" not in ref:
        raise ValueError("Invalid reference")

    modulename, rest = ref.split(":", 1)
    try:
        obj = __import__(modulename, fromlist=[rest])
    except ImportError as exc:
        raise LookupError(f"Error resolving reference {ref}: could not import module") from exc

    try:
        for name in rest.split("."):
            obj = getattr(obj, name)
        return obj
    except Exception:
        raise LookupError(f"Error resolving reference {ref}: error looking up object")


# Suit


def get_project_root(
    start_path: Optional[Path] = None,
    root_marker: Union[str, List[str]] = ["pyproject.toml", "setup.py"],
) -> Optional[Path]:
    """
    Find the root directory of the project by looking for one or more specified marker files.

    Parameters:
        start_path (Optional[Path]): The directory to start searching from. Defaults to the directory containing this script.
        root_marker (Union[str, List[str]]): The filename or list of filenames that mark the root of the project
                                             (e.g., 'pyproject.toml' or ['pyproject.toml', 'setup.py']).

    Returns:
        Optional[Path]: The path to the project root directory, or None if not found.
    """
    start_path = Path(start_path or __file__).resolve()

    markers = [root_marker] if isinstance(root_marker, str) else root_marker
    for parent in [start_path, *start_path.parents]:
        if any((parent / marker).exists() for marker in markers):
            return parent
    return None


def get_suits_base_path() -> Path:
    """
    Returns the path to the plugins folder.
    """
    project_root = get_project_root()
    if project_root is None:
        raise FileNotFoundError("Could not find project root directory.")
    return project_root / "suits"


def get_suit_name(path_to_suit: str) -> str:
    """
    Returns the name of the suit.
    """
    path = Path(path_to_suit)
    return path.name if path.is_dir() else path.stem


# Design Patterns

T = TypeVar("T")


def singleton(cls: Type[T]) -> Callable[..., T]:
    """
    A decorator function that ensures a class has only one instance and provides a global point of access to it.

    Returns:
        Callable[..., T]: The singleton instance of the class.
    """

    instances = {}

    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """
    A decorator that caches the results of the function so future calls with
    the same arguments will return cached results.

    Example:
        @memoize
        def fibonacci(n: int) -> int:
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)
    """
    cache: Dict[Tuple[Any, ...], T] = {}

    def wrapper(*args, **kwargs) -> T:
        key = (args, tuple(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper
