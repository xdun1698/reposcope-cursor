# RepoScope — Cursor Plugin

**Catch the secrets and risky code in your repo — before your AI builds on them.** Free security scanner + token-ranked repo map inside Cursor; Pro adds Cost, Budget (Token Budget Intelligence), Compliance, and a persistent AI game plan.

[![Install — VS Code / Cursor](https://img.shields.io/badge/Install-VS%20Code%20%2F%20Cursor-007ACC?logo=visualstudiocode&logoColor=white)](vscode:extension/nxgentech.reposcope-ai)
[![OpenVSX — Registry](https://img.shields.io/badge/OpenVSX-Registry-C160EF?logo=eclipse&logoColor=white)](https://open-vsx.org/extension/nxgentech/reposcope-ai)
[![Cursor — Marketplace](https://img.shields.io/badge/Cursor-Marketplace-000000?logo=cursor&logoColor=white)](https://cursor.com/marketplace)
![License MIT](https://img.shields.io/badge/license-MIT-green)

![RepoScope AI — Security, Repo Map, Cost, Budget, Compliance, Game Plan](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/hero.png)

> **Local-first:** scans run on your machine via bundled ast-grep. Only anonymous funnel events leave your machine, and you can disable them with `reposcope.telemetry`.

---

## What is RepoScope?

RepoScope is a developer productivity plugin for [Cursor](https://cursor.com) that scans your repo for secrets and risky code, maps it by token cost, and — with Pro — shows what each file costs to analyze with AI. The security scanner and repo map are free on every install.

### Security Scanning — Free

Local, real-time vulnerability detection — **44 detectors** across 14 languages: committed secrets and API/cloud keys (GitHub, Slack, Google, Stripe, JWTs, private keys, DB connection strings, `.env` values), unsafe execution (`eval`, `os.system`, `subprocess`, `child_process`, `Runtime.exec`), framework XSS (`dangerouslySetInnerHTML`, Vue `v-html`, Angular bypass), risky config (permissive CORS, disabled TLS verification), weak crypto, and known-vulnerable npm/pip dependencies. Every finding has a **confidence level** and **CWE ID**; the scan yields a **0–100 security score** with a letter grade and trend. Filter/search/group findings, suppress noise with `.reposcope-ignore`, and export the report to JSON. Best-effort and pattern-based — not a substitute for a professional audit.

![Security Scanner — 44 detectors with severity, confidence, and CWE IDs](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/security-scanner.png)

### Repo Map — Free

Your whole repository at a glance — every source file ranked by token cost with a cost bar, plus the current branch, recent commits, and the files changed in the last commit. Click any file to jump straight to it. Refreshes on save.

![Repo Map — files ranked by token cost with branch and recent-commit context](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/repo-map.png)

### Cost — Pro

Model-agnostic token cost per file, ranked — works across GPT, Claude, and Gemini without locking you into a single provider's tokenizer. Every file ranked by token cost with a cost bar, a breakdown of unused imports / dead code / oversized strings, and cumulative recovered-token tracking via the built-in Tokens Recovered tracker (optional status-bar total, `Copy Recovered-Tokens Summary`). Click any file to open and trim it. In a typical 40K-line TypeScript repo, 4 files often account for 60–70% of the total estimated token budget. Token counts use the industry-standard chars/4 heuristic — model-agnostic estimates within ~10–15% of any specific model's BPE tokenizer, every figure prefixed with `~`.

![Cost — model-agnostic token cost per file, ranked, with a recovered-tokens tracker](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/cost.png)

### Budget — Pro (Token Budget Intelligence)

More than file-level token counts — see exactly what your IDE sends to AI on every prompt, and how fast you're burning through your subscription:

- **Context Overhead Scanner** — estimates the per-prompt token tax from auto-attached rules files, configs, and lockfiles, grouped by category (always-attached only).
- **Rules Audit** — deep analysis of `.cursorrules`, `.windsurfrules`, and `CLAUDE.md`; flags redundant/duplicated/oversized sections and content that belongs in Game Plan, with one-click Move to Game Plan / Remove / Apply All — each with diff preview + undo.
- **Subscription Runway** — configure your plan (Cursor Pro, Claude Pro, Windsurf Pro, or custom) and project when you'll exhaust your monthly token budget, with healthy / caution / critical status. Presets prefill an editable budget, not a provider quota.
- **Optimization Recommendations** — ranked by impact with estimated savings per prompt and per month; apply individually or batch-apply.

All token figures are `~` estimates (~chars/4 heuristic).

![Budget (Token Budget Intelligence) — per-prompt context overhead, rules audit, and subscription runway](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/budget.png)

### Compliance — Pro

Maps your latest Security scan to **OWASP Top 10 (2021)**, **SOC 2 Type II**, and **PCI-DSS v4.0** controls — posture score per framework, per-control PASS / FAIL / PARTIAL / not-covered status, linked findings, a posture trend, and JSON export + copy-summary. Click a control to jump to its findings in Security; Security findings carry an OWASP badge that jumps back. Derived from your existing security results — never a re-scan. **Code-level controls only — a development aid, not a certification tool.** Choose frameworks via `reposcope.compliance.frameworks`.

![Compliance — security findings mapped to OWASP Top 10, SOC 2, and PCI-DSS posture](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/compliance.png)

### Game Plan — Pro

AI-powered goal suggestions based on your repo analysis. Track progress, mark goals complete, and use "Fix with Cursor" to resolve issues directly in the editor.

![AI Game Plan — persistent context across AI sessions](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/game-plan.png)

---

## Install

There are always **two ways to install** — from the marketplace, or manually
from the [Open VSX](https://open-vsx.org/extension/nxgentech/reposcope-ai)
registry. It's the same extension (`nxgentech.reposcope-ai`) either way.

### Cursor

**Way 1 — Cursor Marketplace** _(in review)_
Our Cursor Marketplace listing is pending review. Once approved, search
**"RepoScope"** in `Cmd+Shift+P` → `Cursor: Open Plugin Marketplace` and install
with one click.

**Way 2 — Manual / Open VSX** _(available now)_
Cursor's Extensions panel is backed by Open VSX, where RepoScope is already
published:

1. Open **Extensions** (`Cmd+Shift+X`).
2. Search **RepoScope AI** by publisher **nxgentech** and click **Install**.

Or install the `.vsix` directly:

1. Download the latest `.vsix` from [Open VSX](https://open-vsx.org/extension/nxgentech/reposcope-ai).
2. **Extensions ⋯ → Install from VSIX…** and pick the downloaded file.

### VS Code

**Way 1 — VS Marketplace** — click the **Install** badge above, or search
**RepoScope AI** (publisher **nxgentech**) in the Extensions panel (`Cmd+Shift+X`).

**Way 2 — Manual** — from the Command Palette (`Cmd+Shift+P`) or your terminal:

```
ext install nxgentech.reposcope-ai
code --install-extension nxgentech.reposcope-ai
```

### Windsurf

Windsurf uses Open VSX. Search **RepoScope AI** in the Extensions panel, or
install the `.vsix` from [Open VSX](https://open-vsx.org/extension/nxgentech/reposcope-ai)
via **Install from VSIX…**.

### One-command install (any editor)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/scripts/install.sh)
```

The extension auto-registers the bundled Cursor plugin — hooks, skills, and
commands activate immediately on any repo.

---

## Plugin Structure

```
.cursor-plugin/
├── plugin.json                Plugin manifest (name, version, author, logo)
└── marketplace.json           Multi-plugin marketplace manifest
skills/
├── token_audit.py             Python analysis script (extension webviews)
├── token-audit/SKILL.md       Cursor agent skill definition
├── vuln-scan/SKILL.md         Security scan agent skill
├── repo-trace/SKILL.md        Repo map agent skill
├── game-plan/SKILL.md         Game plan agent skill
└── suggest-goals/SKILL.md     Goal suggestion agent skill
commands/
└── suggest-goals.md           Agent command (goal suggestions)
hooks/
└── hooks.json                 Event-driven automation hooks
assets/
└── reposcope-icon.png        Branding
```

---

## Pricing

| Plan | Price | Included |
|------|-------|----------|
| **Free** | $0 | Security · Repo Map · Unlimited scans · No credit card required |
| **Pro** | $9.99/mo | Everything in Free + Cost · Budget (Token Budget Intelligence) · Compliance · Game Plan · AI goal suggestions · Unlimited scans |
| **Annual** | $89/yr | Same as Pro · Unlimited scans · ~26% savings vs monthly |

<!-- TEAM_LAUNCH_READY: publish the Team + Enterprise rows when the web dashboard ships.
     Team billing is wired ($359/mo flat for 5 seats, beta; AI support agents metered
     at $0.25/interaction beyond 100 included/mo), but we do NOT advertise Team publicly
     until the dashboard is production-grade.

| **Team** | $359/mo (5 seats) | Everything in Pro + multi-repo compliance dashboard · cross-repo posture trends · AI support agents (100 interactions/mo included, $0.25/interaction overage, no hard cap) · team admin |

**Enterprise (5+ seats):** SSO/SAML, custom framework mappings, audit-ready PDF reports, SLA, dedicated support, volume pricing. [Contact us](mailto:hello@reposcope.app).

Team plans include a 14-day trial.
-->


> **Try Pro free for 7 days — no credit card.** Run **RepoScope: Start Free 7-Day Pro Trial** from the Command Palette to unlock Cost (estimated token cost per file), Budget (context overhead, rules audit, subscription runway, recommendations), Compliance (OWASP/SOC 2/PCI-DSS posture), and the AI Game Plan locally.

Manage billing at [reposcope.app](https://reposcope.app).

---

## Support

Questions, bugs, or feedback: **[support@reposcope.app](mailto:support@reposcope.app)**

---

Built by [NxGen Tech Solutions](https://nxgentechsolutions.com)
