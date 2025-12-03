"""Vector database compatibility module.

This module provides backward compatibility for imports of VectorDatabase.
The actual implementation is in vector_store.py.
"""

from .vector_store import VectorDatabase

__all__ = ["VectorDatabase"]

