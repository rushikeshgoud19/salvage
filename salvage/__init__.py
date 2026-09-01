"""salvage — verified AI revenue recovery.

Loads a local `.env` into the environment on import. Both `classify` (LLM key) and `rzp`
(Razorpay keys) read `os.environ` and neither should have to know where the values came
from. `.env` is gitignored: the repo is public and these are live credentials.
Real environment variables always win — a shell export is never overwritten by the file.
"""
import os as _os
import pathlib as _pathlib

def _load_dotenv() -> None:
    path = _pathlib.Path(__file__).resolve().parent.parent / ".env"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return                                  # no .env is the normal case for a clone
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        _os.environ.setdefault(key.strip(), value.strip())

_load_dotenv()
