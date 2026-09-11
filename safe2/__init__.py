"""AI SAFE2 unified CLI."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ai-safe2")
except PackageNotFoundError:  # Source checkout before installation.
    __version__ = "0.3.0.dev0"
