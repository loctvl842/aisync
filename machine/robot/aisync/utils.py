import os
from typing import List

import numpy as np
from numpy.linalg import norm


def get_suits_path() -> str:
    """
    Returns the path to the plugins folder.
    """

    return os.path.join("machine", "robot", "suits")


def get_suit_name(path_to_suit: str) -> str:
    """
    Returns the name of the suit.
    """
    return os.path.basename(path_to_suit)


def cosine_distance(vector_one: List[float], vector_two: List[float]) -> float:
    return 1 - np.dot(np.array(vector_one), np.array(vector_two)) / (
        norm(np.array(vector_one)) * norm(np.array(vector_two))
    )


def l2_distance(vector_one: List[float], vector_two: List[float]) -> float:
    return norm(np.array(vector_one) - np.array(vector_two))


def l1_distance(vector_one: List[float], vector_two: List[float]) -> float:
    return np.sum(np.abs(np.array(vector_one) - np.array(vector_two)))


def max_inner_product(vector_one: List[float], vector_two: List[float]) -> float:
    return np.dot(np.array(vector_one), np.array(vector_two))


# TODO: add all similarity score metrics
def l2_score(vector_one: List[float], vector_two: List[float]) -> float:
    pass


def l1_score(vector_one: List[float], vector_two: List[float]) -> float:
    pass


def max_inner_product_score(vector_one: List[float], vector_two: List[float]) -> float:
    pass


def cosine_similarity_score(vector_one: List[float], vector_two: List[float]) -> float:
    return 1 - cosine_distance(vector_one, vector_two)
