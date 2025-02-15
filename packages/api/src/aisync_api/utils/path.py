from pathlib import Path
from typing import List, Optional, Union


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
