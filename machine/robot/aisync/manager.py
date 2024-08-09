import glob
import os
from typing import List

from core.logger import syslog
from core.utils.decorators import singleton

from .suit import Suit
from .utils import get_suits_path


@singleton
class Manager:
    def __init__(self):
        self.suits_path = get_suits_path()
        self.active_suits = []
        self.suits = self.find_suits()

    def find_suits(self) -> dict[str, "Suit"]:
        """
        Find all suits in the specified path

        Example:
            >>> find_suits()
            {'mark_i': '/path/to/mark_i', 'mark_ii': '/path/to/mark_ii'}
        """

        all_suit_folders = [folder for folder in glob.glob(f"{self.suits_path}/*") if os.path.isdir(folder)]
        suits = {}
        for suit_folder in all_suit_folders:
            syslog(suit_folder)
            suit = self.load_suit(suit_folder)
            suits[suit.name] = suit
            syslog.info(f"Loaded suit: {suit.name}")

            # Activate the suit
            suits[suit.name].activate()
            self.active_suits.append(suit.name)
            syslog.info(f"Activated suit: {suit.name}")
        return suits

    def load_suit(self, path_to_suit: str) -> "Suit":
        """
        Load a suit from the specified path
        """
        try:
            suit = Suit(path_to_suit)
            return suit
        except Exception as e:
            syslog.error(f"Failed to load plugin: {e}")
