import os


def get_suits_path():
    """
    Returns the path to the plugins folder.
    """

    return os.path.join("machine", "robot", "suits")


def get_suit_name(path_to_suit):
    """
    Returns the name of the suit.
    """
    return os.path.basename(path_to_suit)
