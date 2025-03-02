import glob
import os
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

from aisync.log import LogEngine
from aisync.utils import get_suits_base_path

if TYPE_CHECKING:
    from aisync.suit import Suit


class Armory:
    """A place where suits (or armor) are stored and maintained."""

    def __init__(self) -> None:
        self.log = LogEngine(self.__class__.__name__)
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

        try:
            all_suit_paths: list[str] = [
                path for path in glob.glob(f"{self.suits_path}/*") if os.path.isdir(path) or path.endswith(".py")
            ]

            suits: dict[str, "Suit"] = {}
            for path_to_suit in all_suit_paths:
                suit = self.load_suit(path_to_suit)
                suits[suit.name] = suit
                self.log.info(f"Loaded suit: {suit.name}")
            return suits
        except Exception as e:
            self.log.error(f"Error loading suits: {e}")
            self.log.error(traceback.format_exc())
            return {}

    def load_suit(self, path_to_suit: str) -> "Suit":
        """
        Load a suit from the specified path
        """
        from .suit import Suit

        try:
            suit = Suit(path_to_suit)
            return suit
        except Exception as e:
            self.log.error(f"Failed to load plugin: {e}")

    def activate(self, suit_name: str) -> "Suit":
        # Activate the suit
        self.suits[suit_name].activate()
        self.active_suits.append(suit_name)
        self.log.info(f"Activated suit: {suit_name}")
        return self.suits[suit_name]
