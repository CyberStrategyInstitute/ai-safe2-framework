#!/usr/bin/env python3
"""Retired vulnerable entry point; never emit a successful legacy verdict."""
import sys


def main() -> int:
    print("ERROR: The standalone Skill Trust Gate is retired (CSI-2026-001). "
          "Install ai-safe2 0.2.0 or later and use safe2 gate skill PATH --strict. "
          "No scan was performed and no approval was issued.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
