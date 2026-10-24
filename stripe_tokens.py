"""
Stripe js_checksum + rv_timestamp generator.
Ported/simplified from gpt-upi-tool stripe_token.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import urllib.parse
from dataclasses import dataclass
from typing import Any


def caesar_shift(s: str, n: int) -> str:
    return "".join(chr((ord(c) - 32 + n) % 95 + 32) for c in s)


def stripe_encode(s: str) -> str:
    pad = 3 - len(s) % 3
    padded = s + " " * pad
    xored = bytes(5 ^ ord(c) for c in padded)
    return urllib.parse.quote(
        base64.b64encode(xored).decode("ascii"),
        safe="-_.!~*'()",
    )


def _js_stringify(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class StripeTokenConfig:
    bundle_hash: str
    shift: int
    rv_ts: str
    rv: str
    sv: str


def build_token_fields(ppage_id: str, config: StripeTokenConfig) -> dict[str, str]:
    """Build js_checksum + rv_timestamp for confirm payload."""
    js_checksum = caesar_shift(
        stripe_encode(_js_stringify({"id": ppage_id})),
        config.shift,
    )
    rv_timestamp = caesar_shift(
        stripe_encode(
            _js_stringify({"rvTs": config.rv_ts, "rv": config.rv, "sv": config.sv})
        ),
        config.shift,
    )
    return {"js_checksum": js_checksum, "rv_timestamp": rv_timestamp}


# Fallback constants (may go stale when Stripe rotates bundles).
# Live extract is preferred when possible.
_FALLBACK = StripeTokenConfig(
    bundle_hash="fallback",
    shift=11,
    rv_ts="2024-01-01 00:00:00 -0000",
    rv="e5ebd5e1e6fallback0000000000000003",
    sv="3c7ef39815fallback0000000000000069",
)


_JS_CHECKSUM_RE = re.compile(
    r"\b(?P<fn>[a-zA-Z_$][\w$]{0,3})\s*\(\s*"
    r"\(\s*0\s*,\s*(?P<encmod>[a-zA-Z_$][\w$]{0,3})\s*\.\s*(?P<encfn>[a-zA-Z_$][\w$]{0,3})\s*\)"
    r"\s*\(\s*JSON\s*\.\s*stringify\s*\(\s*\{\s*id\s*:\s*[a-zA-Z_$][\w$]*\s*\}\s*\)\s*\)"
    r"\s*,\s*(?P<shift>\d+)\s*\)"
)


def try_extract_from_bundle(js_source: str) -> StripeTokenConfig | None:
    """Best-effort extract shift + constants from Stripe custom-checkout JS."""
    m = _JS_CHECKSUM_RE.search(js_source)
    if not m:
        return None
    shift = int(m.group("shift"))
    # Try to find rvTs / rv / sv-like string constants (loose)
    rv_ts = None
    rv = None
    sv = None
    for pat, name in [
        (r'"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} -0000)"', "rv_ts"),
        (r'"([a-f0-9]{20,})"', "hash"),
    ]:
        found = re.findall(pat, js_source)
        if name == "rv_ts" and found:
            rv_ts = found[0]
        if name == "hash" and len(found) >= 2:
            rv, sv = found[0], found[1]
    if not (rv_ts and rv and sv):
        return None
    h = hashlib.sha256(js_source.encode("utf-8", errors="ignore")).hexdigest()
    return StripeTokenConfig(bundle_hash=h, shift=shift, rv_ts=rv_ts, rv=rv, sv=sv)


def get_config(js_source: str | None = None) -> StripeTokenConfig:
    if js_source:
        cfg = try_extract_from_bundle(js_source)
        if cfg:
            return cfg
    return _FALLBACK
