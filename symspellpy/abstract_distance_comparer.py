from abc import ABC, abstractmethod


class AbstractDistanceComparer(ABC):
    """An interface to compute relative distance between two strings."""

    @abstractmethod
    def distance(self, string_1: str, string_2: str, max_distance: int) -> int:
        """Returns a measure of the distance between two strings.

        Args:
            string_1: One of the strings to compare.
            string_2: The other string to compare.
            max_distance: The maximum distance that is of interest.

        Returns:
            -1 if the distance is greater than the max_distance, 0 if the strings
                are equivalent, otherwise a positive number whose magnitude
                increases as difference between the strings increases.
        """
