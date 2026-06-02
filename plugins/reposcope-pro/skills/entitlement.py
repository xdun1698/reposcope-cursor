"""License/entitlement helper for Pro RepoScope skills.

Free skills (``token_audit``, ``repo_trace``) never import this. Pro skills
(``vuln_scan``, ``game_plan``, ``parse_suggested_goals``) call
:func:`require_pro` at the top of their ``_main()``; when license enforcement is
enabled and the resolved tier is not ``pro``/``team``, they emit an upsell JSON
object and exit instead of producing results.

Enforcement is OFF by default in the monorepo so that:
  * the Insight server (which already gates via the Stripe entitlement
    middleware before invoking a skill) behaves normally, and
  * the unit tests and the VS Code extension keep working unchanged.

The published standalone Pro plugin ships with enforcement ON — the
``sync-public-plugin.sh`` assembly step flips ``_DEFAULT_REQUIRED`` to ``"1"``
in the copied file. Either context can override via the
``REPOSCOPE_LICENSE_REQUIRED`` environment variable.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

# Sync flips this to "1" for the published Pro plugin (see sync-public-plugin.sh).
_DEFAULT_REQUIRED = "1"

DEFAULT_SERVER_BASE = "https://codewalker-server-production.up.railway.app"
PRICING_URL = "https://reposcope.app/pricing.html"
_TIMEOUT_S = 5
_FALSEY = frozenset({"", "0", "false", "no", "off"})


def enforcement_enabled() -> bool:
    """True when Pro skills should require a valid license before running."""
    raw = os.environ.get("REPOSCOPE_LICENSE_REQUIRED", _DEFAULT_REQUIRED)
    return raw.strip().lower() not in _FALSEY


def resolve_license_key() -> str | None:
    """Stripe customer id (``cus_…``): ``REPOSCOPE_LICENSE_KEY`` env, then a
    ``.reposcope-license`` file in the current working directory."""
    key = os.environ.get("REPOSCOPE_LICENSE_KEY", "").strip()
    if key:
        return key
    try:
        content = (Path.cwd() / ".reposcope-license").read_text(encoding="utf-8").strip()
        if content:
            return content
    except OSError:
        pass
    return None


def resolve_team_key() -> str | None:
    """Shared team gate secret (pairs with the server ``REPOSCOPE_TEAM_GATE_KEY``)."""
    key = os.environ.get("REPOSCOPE_TEAM_GATE_KEY", "").strip()
    return key or None


def resolve_server_base() -> str:
    base = os.environ.get("REPOSCOPE_SERVER_URL", "").strip() or DEFAULT_SERVER_BASE
    return base.rstrip("/")


def get_tier() -> str:
    """Resolve the tier via ``GET /api/v1/entitlement``. Returns ``"free"`` when
    no license is configured or on any network/parse failure."""
    key = resolve_license_key()
    team = resolve_team_key()
    if not key and not team:
        return "free"

    url = resolve_server_base() + "/api/v1/entitlement"
    headers = {"Accept": "application/json"}
    if key:
        url += "?" + urllib.parse.urlencode({"customerId": key})
    elif team:
        headers["x-reposcope-team-key"] = team

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
        tier = payload.get("tier")
        return tier if tier in ("free", "pro", "team") else "free"
    except Exception:
        return "free"


def upsell(feature: str, tier: str = "free") -> dict:
    """Structured response returned by a Pro skill when the caller is not entitled."""
    return {
        "error": "pro_required",
        "feature": feature,
        "tier": tier,
        "upgradeUrl": PRICING_URL,
        "message": (
            f"{feature} is a RepoScope Pro feature. Upgrade at {PRICING_URL}, then set "
            "REPOSCOPE_LICENSE_KEY (your Stripe customer id) or add a .reposcope-license "
            "file to your workspace root to unlock it."
        ),
    }


def require_pro(feature: str) -> tuple[bool, dict | None]:
    """Gate a Pro feature.

    Returns ``(True, None)`` when the caller may proceed — either enforcement is
    disabled (monorepo/server/tests) or the resolved tier is ``pro``/``team``.
    Otherwise returns ``(False, upsell_dict)`` for the skill to print and exit.
    """
    if not enforcement_enabled():
        return True, None
    tier = get_tier()
    if tier in ("pro", "team"):
        return True, None
    return False, upsell(feature, tier)
