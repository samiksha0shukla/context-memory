import math
from typing import List


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Calculate the cosine similarity b/w two embedding vectors
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)