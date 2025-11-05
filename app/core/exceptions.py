# app/core/exceptions.py
class NodeNotFoundException(Exception):
    """Raised when a node is not found for a given user or ID."""
    pass