import numpy as np
from sklearn.metrics import pairwise_distances


class KeyboardDistance:

    qwerty_layout = [
        ['`~¬', '1!≠', '2@²', '3#³', '4$¢', '5%€', '6^½', '7&§', '8*·', '9(«', '0)»', '-_–', '=+'],
        ['\t',  'qQπ', 'wWœ', 'eEę', 'rR©', 'tTß', 'yY←', 'uU↓', 'iI→', 'oOó', 'pPþ', '[{', ']}', '\\|'],
               ['aAą', 'sSś', 'dDð', 'fFæ', 'gGŋ', 'hH’', 'jJə', 'kK…', 'lLł', ';:', '\'"'],
                   ['zZż', 'xXź', 'cCć', 'vV„', 'bB”', 'nNń', 'mMµ', ',<≤', '.>≥', '/?'],
                                 [' ',   ' ',   ' ',   ' ',   ' ']
    ]


    def __init__(self, metric="euclidean"):
        self.metric = metric
        self._qwerty_chars = {
            char
            for line in self.qwerty_layout
            for key in line
            for char in key
        }
        self._non_qwerty_ascii_chars = {
            chr(idx)
            for idx in range(128)
            if chr(idx) not in self._qwerty_chars
        }
        self.char_coords = self._qwerty_char_coords()
        self.ascii_chars_distance = np.array([
            [self.char2char_distance(chr(x), chr(y), self.metric) for x in range(128)]
            for y in range(128)
        ])

    def _single_char_coords(self, char):
        qwerty_line_shift = {0: 0, 1: 0, 2: 2, 3: 3, 4: 5}
        return [
            (x + qwerty_line_shift[y], y)
            for (y, row) in enumerate(self.qwerty_layout)
            for (x, key) in enumerate(row)
            if char in key
        ]

    def _qwerty_char_coords(self):
        char_coords = {
            char: self._single_char_coords(char)
            for char in self._qwerty_chars
        }
        for char in self._non_qwerty_ascii_chars:
            char_coords[char] = [(-1, -1)]
        return char_coords

    def char2char_distance(self, char1, char2, metric="euclidean"):
        distances = pairwise_distances(self.char_coords[char1], self.char_coords[char2], metric=metric)
        return distances.min()


if __name__ == '__main__':

    for metric in ("euclidean", "manhattan"):
        keyboard = KeyboardDistance(metric=metric)
        print(keyboard._qwerty_chars)
        print(keyboard._non_qwerty_ascii_chars)
        print(
            keyboard.ascii_chars_distance.shape,
            keyboard.ascii_chars_distance.min(),
            keyboard.ascii_chars_distance.max(),
            keyboard.ascii_chars_distance.mean()
        )
