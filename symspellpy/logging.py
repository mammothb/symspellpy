# MIT License
#
# Copyright (c) 2025 mmb L (Python port)
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

import logging
import sys

logger = logging.getLogger("symspellpy")

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(
    logging.Formatter(fmt="%(asctime)s: %(levelname).1s %(name)s] %(message)s")
)

logger.addHandler(handler)
