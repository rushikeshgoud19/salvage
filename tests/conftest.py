"""Shared pytest setup.

Seed-commit file. Neither lane owns it, neither lane edits it — a change request goes
through `.agents/BLOCKERS.md`. It exists only so `import salvage` works when the package
has not been pip-installed, which is the state a fresh clone is in.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
