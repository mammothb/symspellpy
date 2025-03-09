# MIT License
#
# Copyright (c) 2025 mmb L (Python port)
# Copyright (c) 2021 Wolf Garbe (Original C# implementation)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

"""
.. module:: pickle_mixing
   :synopsis: Mixin to provide pickle loading and saving functionalities.
"""

import gzip
import logging
import pickle
from operator import itemgetter
from pathlib import Path
from typing import IO, Optional, Union, cast

logger = logging.getLogger(__name__)


# Protocol only available in py38
# class SymSpellProtocol(Protocol):
#     data_version: int
#     _count_threshold: int
#     _max_dictionary_edit_distance: int
#     _prefix_length: int
#     _deletes: dict[str, list[str]]
#     _words: dict[str, int]
#     _max_length: int


class PickleMixin:
    """Implements saving and loading pickle functionality for SymSpell."""

    data_version: int
    _below_threshold_words: dict[str, int]
    _bigrams: dict[str, int]
    _deletes: dict[str, list[str]]
    _words: dict[str, int]

    _count_threshold: int
    _max_dictionary_edit_distance: int
    _max_length: int
    _prefix_length: int

    def load_pickle(
        self,
        data: Union[bytes, Path],
        compressed: bool = True,
        from_bytes: bool = False,
    ) -> bool:
        """Loads delete combination from file as pickle. This will reduce the
        loading time compared to running :meth:`load_dictionary` again.

        Args:
            data: Either bytes string to be used with ``from_bytes=True`` or the
                path+filename of the pickle file to be used with
                ``from_bytes=False``.
            compressed: A flag to determine whether to read the pickled data as
                compressed data.
            from_bytes: Flag to determine if we are loading from bytes or file.

        Returns:
            ``True`` if delete combinations are successfully loaded.
        """
        if from_bytes:
            assert isinstance(data, bytes)
            return self._load_pickle_stream(data, from_bytes)
        if compressed:
            with gzip.open(data, "rb") as gzip_infile:
                return self._load_pickle_stream(cast(IO[bytes], gzip_infile))
        else:
            with open(data, "rb") as infile:
                return self._load_pickle_stream(infile)

    def save_pickle(
        self,
        filename: Optional[Path] = None,
        compressed: bool = True,
        to_bytes: bool = False,
    ) -> Optional[bytes]:
        """Pickles :attr:`_deletes`, :attr:`_words`, and :attr:`_max_length` into
        a stream for quicker loading later.

        Args:
            filename: The path+filename of the pickle file.
            compressed: A flag to determine whether to compress the pickled data.
            to_bytes: Flag to determine by bytes string should be returned
                instead of wrting to file.

        Returns:
            A byte string of the pickled data if ``to_bytes=True``.
        """
        if to_bytes:
            return self._save_pickle_stream(to_bytes=to_bytes)
        assert filename is not None
        if compressed:
            with gzip.open(filename, "wb") as gzip_outfile:
                self._save_pickle_stream(cast(IO[bytes], gzip_outfile))
        else:
            with open(filename, "wb") as outfile:
                self._save_pickle_stream(outfile)
        return None

    def _load_pickle_stream(
        self, stream: Union[bytes, IO[bytes]], from_bytes: bool = False
    ) -> bool:
        """Loads delete combination from stream as pickle. This will reduce the
        loading time compared to running :meth:`load_dictionary` again.

        **NOTE**: Prints warning if the current settings `count_threshold`,
        `max_dictionary_edit_distance`, and `prefix_length` are different from
        the loaded settings. Overwrite current settings with loaded settings.

        Args:
            stream: The stream from which the pickle data is loaded.
            from_bytes: Flag to determine if we are loading from bytes or file.

        Returns:
            ``True`` if delete combinations are successfully loaded.
        """
        if from_bytes:
            assert isinstance(stream, bytes)
            pickle_data = pickle.loads(stream)  # nosec
        else:
            assert not isinstance(stream, bytes)
            pickle_data = pickle.load(stream)  # nosec
        if pickle_data.get("data_version", None) != self.data_version:
            return False
        settings = ("count_threshold", "max_dictionary_edit_distance", "prefix_length")
        if itemgetter(*settings)(pickle_data) != (
            self._count_threshold,
            self._max_dictionary_edit_distance,
            self._prefix_length,
        ):
            logger.warning(
                f"Loading data which was created using different {settings} settings. Overwriting current SymSpell instance with loaded settings ..."
            )
        self._deletes = pickle_data["deletes"]
        self._words = pickle_data["words"]
        self._max_length = pickle_data["max_length"]
        # dictionary entries related variables
        self._below_threshold_words = pickle_data["below_threshold_words"]
        self._bigrams = pickle_data["bigrams"]
        self._deletes = pickle_data["deletes"]
        self._words = pickle_data["words"]
        self._max_length = pickle_data["max_length"]
        # SymSpell settings used to generate the above
        self._count_threshold = pickle_data["count_threshold"]
        self._max_dictionary_edit_distance = pickle_data["max_dictionary_edit_distance"]
        self._prefix_length = pickle_data["prefix_length"]
        return True

    def _save_pickle_stream(
        self, stream: Optional[IO[bytes]] = None, to_bytes: bool = False
    ) -> Optional[bytes]:
        """Pickles :attr:`_below_threshold_words`, :attr:`_bigrams`,
        :attr:`_deletes`, :attr:`_words`, and :attr:`_max_length` into
        a stream for quicker loading later.

        Pickles :attr:`_count_threshold`, :attr:`_max_dictionary_edit_distance`,
        and :attr:`_prefix_length` to ensure consistent behavior.

        Args:
            stream: The stream to store the pickle data.
            to_bytes: Flag to determine by bytes string should be returned
                instead of wrting to file.

        Returns:
            A byte string of the pickled data if ``to_bytes=True``.
        """
        pickle_data = {
            # Dictionary entries related variables
            "below_threshold_words": self._below_threshold_words,
            "bigrams": self._bigrams,
            "deletes": self._deletes,
            "words": self._words,
            "max_length": self._max_length,
            # SymSpell settings used to generate the above
            "count_threshold": self._count_threshold,
            "max_dictionary_edit_distance": self._max_dictionary_edit_distance,
            "prefix_length": self._prefix_length,
            # Version to ensure compatibility
            "data_version": self.data_version,
        }
        if to_bytes:
            return pickle.dumps(pickle_data)
        assert stream is not None
        pickle.dump(pickle_data, stream)
        return None
