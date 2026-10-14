"""Schema compatibility across supported Home Assistant releases."""

try:
    import probatio as vol
except ImportError:
    import voluptuous as vol

__all__ = ["vol"]
