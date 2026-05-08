"""Logging setup for jeff.

Provides a single ``get_logger`` function that returns a stdlib logger.
Verbose mode switches from WARNING to DEBUG.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def setup(verbose: bool = False) -> None:
    """Configure the root jeff logger.

    Call once at CLI startup. Subsequent calls are no-ops.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return
    _CONFIGURED = True

    level = logging.DEBUG if verbose else logging.WARNING
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    logger = logging.getLogger("jeff")
    logger.setLevel(level)
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the ``jeff`` namespace."""
    return logging.getLogger(f"jeff.{name}")
