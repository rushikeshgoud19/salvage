"""Razorpay boundary — direct REST over httpx, no SDK (Contract §6).

The failure this module prevents, and demonstrates: **a `201` from a create call is not
a recovery.** Issuing a payment link is an action; money arriving is a fact. The two are
different calls with different answers, and every naive recovery agent conflates them.

## The engineered failure (deterministic, and the point of the demo)

In offline mode a cohort of records — decided by hashing the payment id, so it is stable
across runs and independent of iteration order — gets a **well-formed `201`** from
`create_payment_link`, with a real-looking `plink_` id and a `short_url`, and then
`fetch_payment_link` reports `status="created", amount_paid=0` **forever**. Nothing about
the create response distinguishes them. An agent that books recoveries on the create call
books every one of them; salvage re-fetches, sees `created/0`, seals `verified=False`, and
their rupees land in `verification_gap_paise` instead of in the headline.

The cohort is `_STUCK_PCT` percent of the links this client issues (≈8 links of a
240-record batch once the policy has decided which records get a link). Link ids are a
pure function of the payment id and cohort membership is a pure function of the link id,
so the same batch produces the same cohort on every run, on any machine.

The other two offline fates are ordinary: a link either pays (`status="paid"`,
`amount_paid == amount`) or lapses (`status="expired"`, `amount_paid=0`). Only the
engineered cohort sits at `created/0` indefinitely, which is what makes it legible in
`RESULTS.md` without a human narrating it.

## Fixtures

`offline=True` is the default and the demo path: it reads recorded response bodies from
`fixtures/<endpoint>__<key>.json` and performs zero network calls. The recording *shape*
comes from the fixture; the identifiers, amounts and statuses are substituted from typed
Python values in this module, never from anything a model wrote.

`offline=False` demands both `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` and raises at
construction naming whichever is missing. There is no silent fallback: falling back to a
fixture when the network was requested would report a fake recovery, which is the one
thing this project may not ship. Online mode *is* record mode — every response body it
receives is written back into `fixtures/`, so the fixture set is refreshed from real
test-mode traffic the moment keys exist.

Known limitation: `fetch_payment(rzp_payment_id)` is passed only an id, so offline it
cannot know the record's amount and echoes the recorded one. Verify a RETRY on
`status == "captured"`; do not gate it on that echoed `amount`.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import httpx

_BASE_URL = "https://api.razorpay.com/v1"
_TIMEOUT_S = 20.0

# Share of issued links that never leave `created`. Tuned so that a 240-record batch,
# of which roughly half earns a payment link, yields the ~8-record demo cohort.
_STUCK_PCT = 6
# Share of the remaining links that actually pay. Sits inside the published 45-65% band
# for reason-specific recovery (Contract §10.2); it is the single knob for offline yield.
_PAID_PCT = 62
# Share of retried payments that capture. Soft declines approve on roughly one properly
# timed second attempt in five (Contract §10.2), plus the transient-downtime retries.
_CAPTURED_PCT = 38


def _bucket(salt: str, key: str) -> int:
    """Stable 0-99 bucket. Deterministic across processes — `hash()` is not."""
    digest = hashlib.sha256(f"{salt}:{key}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def _link_id(payment_id: str) -> str:
    """A real-looking `plink_` id that is a pure function of the payment id."""
    digest = hashlib.sha256(f"plink:{payment_id}".encode("utf-8")).hexdigest()
    return "plink_" + digest[:14]


def _is_stuck(link_id: str) -> bool:
    """Membership in the engineered cohort — created succeeds, money never arrives."""
    return _bucket("stuck", link_id) < _STUCK_PCT


def _paise(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field} must be integer paise; observed {value!r} of type {type(value).__name__}"
        )
    return value


class RzpClient:
    """Razorpay payment links and payments. Offline by default; never falls back silently."""

    def __init__(self, offline: bool = True, fixtures_dir: str = "fixtures") -> None:
        self.offline = offline
        self.fixtures_dir = fixtures_dir
        self._issued: dict[str, dict[str, Any]] = {}
        self._http: httpx.Client | None = None
        if offline:
            return
        missing = [name for name in ("RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET")
                   if not os.environ.get(name)]
        if missing:
            raise RuntimeError(
                "RzpClient(offline=False) needs live Razorpay credentials; missing "
                + " and ".join(missing)
                + f". Use offline=True to replay recorded fixtures from {fixtures_dir!r} —"
                " this client will not fall back on its own, because a fixture answered in"
                " place of the gateway is a fake recovery."
            )
        self._http = httpx.Client(
            base_url=_BASE_URL,
            auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_KEY_SECRET"]),
            timeout=_TIMEOUT_S,
        )

    # -- public surface (Contract §4) ---------------------------------------------------

    def create_payment_link(self, payment_id: str, amount_paise: int, email: str) -> dict:
        """Issue a fresh link. A success here is an ACTION, never a recovery."""
        _paise(amount_paise, "amount_paise")
        if self._http is not None:
            return self._request(
                "POST", "/payment_links", "payment_links",
                json={
                    "amount": amount_paise,
                    "currency": "INR",
                    "reference_id": payment_id,
                    "description": "Salvage recovery link",
                    "customer": {"email": email},
                    # Nothing in this project reaches a real person (PLAN, out of scope).
                    "notify": {"sms": False, "email": False},
                },
            )
        body = self._fixture("payment_links", "create")
        link_id = _link_id(payment_id)
        body.update(
            id=link_id,
            amount=amount_paise,
            amount_paid=0,
            status="created",
            reference_id=payment_id,
            short_url=f"https://rzp.io/i/{link_id[6:14]}",
        )
        body["customer"] = {**body.get("customer", {}), "email": email}
        self._issued[link_id] = body
        return body

    def fetch_payment_link(self, link_id: str) -> dict:
        """Re-read the link from the provider. This call, not the create, decides money."""
        if self._http is not None:
            body = self._request("GET", f"/payment_links/{link_id}", "payment_links")
            return body
        issued = self._issued.get(link_id)
        if issued is None:
            raise LookupError(
                f"no recorded create for {link_id!r} in this offline session; offline"
                " fetch replays links this client issued, so create_payment_link must run"
                " first"
            )
        amount = int(issued["amount"])
        if _is_stuck(link_id):
            # The engineered cohort: the create call was well-formed and the money never
            # comes. It stays `created` on every fetch, for the life of the run.
            body = self._fixture("payment_links", "created")
            body.update(id=link_id, amount=amount, amount_paid=0, status="created",
                        reference_id=issued.get("reference_id", ""))
            return body
        if _bucket("paid", link_id) < _PAID_PCT:
            body = self._fixture("payment_links", "paid")
            body.update(id=link_id, amount=amount, amount_paid=amount, status="paid",
                        reference_id=issued.get("reference_id", ""))
            return body
        body = self._fixture("payment_links", "expired")
        body.update(id=link_id, amount=amount, amount_paid=0, status="expired",
                    reference_id=issued.get("reference_id", ""))
        return body

    def fetch_payment(self, rzp_payment_id: str) -> dict:
        """Re-read a payment. `status == "captured"` is the only reading that means money."""
        if self._http is not None:
            return self._request("GET", f"/payments/{rzp_payment_id}", "payments")
        captured = _bucket("captured", rzp_payment_id) < _CAPTURED_PCT
        body = self._fixture("payments", "captured" if captured else "failed")
        body["id"] = rzp_payment_id
        return body

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    # -- internals ----------------------------------------------------------------------

    def _request(self, method: str, path: str, endpoint: str, **kwargs: Any) -> dict:
        assert self._http is not None  # online path only; offline never reaches here
        response = self._http.request(method, path, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(
                f"razorpay {method} {path} returned {response.status_code}:"
                f" {response.text[:200]}"
            )
        body = response.json()
        self._record(endpoint, body)
        return body

    def _record(self, endpoint: str, body: dict) -> None:
        """Online mode is record mode (Contract §6): keep the real body as the fixture."""
        key = str(body.get("status") or "create")
        os.makedirs(self.fixtures_dir, exist_ok=True)
        path = os.path.join(self.fixtures_dir, f"{endpoint}__{key}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(body, handle, indent=2, sort_keys=True)

    def _fixture(self, endpoint: str, key: str) -> dict:
        path = os.path.join(self.fixtures_dir, f"{endpoint}__{key}.json")
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"no fixture at {path}; offline mode replays recorded bodies only."
                " Run with RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET set to record it."
            ) from exc
