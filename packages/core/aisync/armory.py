import glob
import os
from pathlib import Path
from typing import TYPE_CHECKING

from aisync.log import log
from aisync.utils import get_suits_base_path

if TYPE_CHECKING:
    from aisync.suit import Suit


class Armory:
    """A place where suits (or armor) are stored and maintained."""

    def __init__(self) -> None:
        self.suits_path = get_suits_base_path()
        self.active_suits = []
        self.suits = self.find_suits()

    def find_suits(self) -> dict[str, "Suit"]:
        """
        Find all suits in the specified path

        Example:
            >>> find_suits()
            {'mark_i': '/path/to/mark_i', 'mark_ii': '/path/to/mark_ii'}
        """

        assert Path(self.suits_path).exists(), f"Path '{self.suits_path}' does not exist."

        all_suit_folders: list[str] = [folder for folder in glob.glob(f"{self.suits_path}/*") if os.path.isdir(folder)]
        # all_suit_folders.append('/home/loc/Documents/Work/Rockship/repositories/loctvl842/aisync/packages/core/suits/mark_ii.py')

        suits: dict[str, "Suit"] = {}
        for suit_folder in all_suit_folders:
            suit = self.load_suit(suit_folder)
            suits[suit.name] = suit
            log.info(f"Loaded suit: {suit.name}")

            # Activate the suit
            suits[suit.name].activate()
            self.active_suits.append(suit.name)
            log.info(f"Activated suit: {suit.name}")
        return suits

    def load_suit(self, path_to_suit: str) -> "Suit":
        """
        Load a suit from the specified path
        """
        from .suit import Suit

        try:
            suit = Suit(path_to_suit)
            return suit
        except Exception as e:
            log.error(f"Failed to load plugin: {e}")
