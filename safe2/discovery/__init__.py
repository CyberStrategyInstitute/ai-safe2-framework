"""Local-first discovery for agent harnesses and execution environments."""

from .assets import inventory_assets
from .card import render_environment_html, render_environment_markdown
from .config import inspect_inventory
from .drift import compare_discovery, load_baseline
from .integrity import inventory_digest, seal_inventory, verify_inventory
from .local import discover_local
from .policy import evaluate_policy, load_policy
from .posix import probe_ssh, probe_wsl
from .posture import assess_posture

__all__ = [
    "assess_posture",
    "compare_discovery",
    "discover_local",
    "evaluate_policy",
    "inspect_inventory",
    "inventory_assets",
    "inventory_digest",
    "load_baseline",
    "load_policy",
    "probe_ssh",
    "probe_wsl",
    "render_environment_html",
    "render_environment_markdown",
    "seal_inventory",
    "verify_inventory",
]
