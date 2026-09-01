"""`python -m salvage` — the only entry point a reviewer is asked to type.

Exists so the demo runs from a clean checkout with no install step: `pip install -e .`
gives the `salvage` script, but a reviewer who just cloned the repo gets the same app
here.
"""
from __future__ import annotations

from salvage.cli import app

if __name__ == "__main__":
    app()
