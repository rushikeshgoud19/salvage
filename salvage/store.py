"""SQLite system of record for the recovery loop.

The failure this module prevents: booking a recovery that never happened. A row in
`settlements` is the durable claim "money arrived for this payment", and stepproof
verifiers read that table through `sqlite_row_exists` — so a row written on the strength
of a `201` from a create call would launder a claim into evidence. The only writer is
`mark_settled`, and it refuses a row with no provider reference or a non-positive amount.

Money is integer paise throughout; every money argument is type-checked on the way in,
because a float rupee that reaches this table becomes a rounding bug in a recovery figure.
"""
from __future__ import annotations

import os
import sqlite3
import time

from salvage.types import ActionKind, FailedPayment

# Contract §8, verbatim. Verifiers read these tables, so the shape is contract, not detail.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    payment_id   TEXT PRIMARY KEY,
    order_id     TEXT NOT NULL,
    customer_id  TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    failed_at    REAL NOT NULL,
    gateway_code TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id   TEXT NOT NULL REFERENCES payments(payment_id),
    kind         TEXT NOT NULL,
    provider_ref TEXT NOT NULL DEFAULT '',
    cost_paise   INTEGER NOT NULL DEFAULT 0,
    created_at   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS settlements (
    payment_id    TEXT PRIMARY KEY REFERENCES payments(payment_id),
    provider_ref  TEXT NOT NULL,
    amount_paise  INTEGER NOT NULL,
    settled_at    REAL NOT NULL
);
"""


def _paise(value: object, field: str) -> int:
    """Reject anything that is not an integer number of paise.

    `bool` is an `int` subclass in Python, hence the explicit exclusion — `True` paise
    would store as 1 and read back as a rupee of recovered revenue.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field} must be integer paise; observed {value!r} of type {type(value).__name__}"
        )
    return value


class Store:
    """The recovery loop's only durable state. One SQLite file per run (Contract §9.5)."""

    def __init__(self, path: str) -> None:
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        self._path = path
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(_SCHEMA)
        self._db.commit()

    def upsert_payment(self, p: FailedPayment) -> None:
        _paise(p.amount_paise, "amount_paise")
        self._db.execute(
            """
            INSERT INTO payments (payment_id, order_id, customer_id, amount_paise,
                                  failed_at, gateway_code)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(payment_id) DO UPDATE SET
                order_id     = excluded.order_id,
                customer_id  = excluded.customer_id,
                amount_paise = excluded.amount_paise,
                failed_at    = excluded.failed_at,
                gateway_code = excluded.gateway_code
            """,
            (p.payment_id, p.order_id, p.customer_id, p.amount_paise,
             float(p.failed_at), p.gateway_code),
        )
        self._db.commit()

    def record_attempt(self, payment_id: str, kind: ActionKind,
                       provider_ref: str, cost_paise: int) -> int:
        """Record that an action was taken. Returns the attempt row id.

        An attempt is a *claim*, not a settlement: it is written whether or not money
        ever arrives, and nothing here may be read as recovered revenue.
        """
        _paise(cost_paise, "cost_paise")
        cur = self._db.execute(
            "INSERT INTO attempts (payment_id, kind, provider_ref, cost_paise, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (payment_id, kind.value, provider_ref, cost_paise, time.time()),
        )
        self._db.commit()
        return int(cur.lastrowid)

    def mark_settled(self, payment_id: str, provider_ref: str, amount_paise: int) -> None:
        """Write the settlement row. Call ONLY after the provider confirmed money arrived.

        Both guards below exist because this row is what a verifier trusts (Contract §8):
        a settlement with no provider reference cannot be re-checked against the gateway,
        and a non-positive amount is not a recovery in any currency.
        """
        if not provider_ref:
            raise ValueError(
                f"refusing to settle {payment_id}: provider_ref is empty, so this settlement"
                " could never be re-checked against the gateway"
            )
        _paise(amount_paise, "amount_paise")
        if amount_paise <= 0:
            raise ValueError(
                f"refusing to settle {payment_id}: observed amount_paise={amount_paise},"
                " expected a positive integer"
            )
        self._db.execute(
            """
            INSERT INTO settlements (payment_id, provider_ref, amount_paise, settled_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(payment_id) DO UPDATE SET
                provider_ref = excluded.provider_ref,
                amount_paise = excluded.amount_paise,
                settled_at   = excluded.settled_at
            """,
            (payment_id, provider_ref, amount_paise, time.time()),
        )
        self._db.commit()

    def attempts_for(self, payment_id: str) -> int:
        row = self._db.execute(
            "SELECT COUNT(*) AS n FROM attempts WHERE payment_id = ?", (payment_id,)
        ).fetchone()
        return int(row["n"])

    def spend_for(self, payment_id: str) -> int:
        row = self._db.execute(
            "SELECT COALESCE(SUM(cost_paise), 0) AS spent FROM attempts WHERE payment_id = ?",
            (payment_id,),
        ).fetchone()
        return int(row["spent"])

    def close(self) -> None:
        self._db.close()
