# RepoScope — Cursor Plugin

**See your code. Know its cost. Ship smarter.** — AI Cost Intelligence: token waste, security, a token-ranked repo map, and persistent AI context, right inside Cursor.

[![Install — VS Code / Cursor](https://img.shields.io/badge/Install-VS%20Code%20%2F%20Cursor-007ACC?logo=visualstudiocode&logoColor=white)](vscode:extension/nxgentech.reposcope-ai)
[![OpenVSX — Registry](https://img.shields.io/badge/OpenVSX-Registry-C160EF?logo=eclipse&logoColor=white)](https://open-vsx.org/extension/nxgentech/reposcope-ai)
[![Cursor — Marketplace](https://img.shields.io/badge/Cursor-Marketplace-000000?logo=cursor&logoColor=white)](https://cursor.com/marketplace)
![License MIT](https://img.shields.io/badge/license-MIT-green)

![RepoScope AI — Token Waste, Security Scanner, Repo Map, Game Plan](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/hero.png)

> **Local-first:** scans run on your machine via bundled ast-grep. Only anonymous funnel events leave your machine, and you can disable them with `reposcope.telemetry`.

---

## What is RepoScope?

RepoScope is a developer productivity plugin for [Cursor](https://cursor.com) that helps you understand large codebases, eliminate LLM token waste, and catch security issues before they ship.

### Token Waste Detection

See exactly which files eat your LLM context budget. BPE-accurate token counts per file let you prune intelligently before sending code to any AI model — saving money and improving output quality.

Track cumulative savings across scans with the built-in Estimated Savings tracker — each re-scan tallies the tokens you've recovered and an estimated dollar amount. Configurable API rate (`reposcope.apiRate`) to match your provider, an optional status-bar total, and a `Copy Savings Summary` command. All local; dollar figures are estimates.

In a typical 40K-line TypeScript repo, 4 files often account for 60–70% of the total BPE token budget — usually auto-generated code or config blobs. Excluding them from AI context means cleaner answers and lower API bills.

![Token Waste Analysis — ranked by BPE token cost with estimated savings](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/token-waste.png)

### Security Scanning

Local, real-time vulnerability detection — **44 detectors** across 14 languages: committed secrets and API/cloud keys (GitHub, Slack, Google, Stripe, JWTs, private keys, DB connection strings, `.env` values), unsafe execution (`eval`, `os.system`, `subprocess`, `child_process`, `Runtime.exec`), framework XSS (`dangerouslySetInnerHTML`, Vue `v-html`, Angular bypass), risky config (permissive CORS, disabled TLS verification), weak crypto, and known-vulnerable npm/pip dependencies. Every finding has a **confidence level** and **CWE ID**; the scan yields a **0–100 security score** with a letter grade and trend. Filter/search/group findings, suppress noise with `.reposcope-ignore`, and export the report to JSON. Best-effort and pattern-based — not a substitute for a professional audit.

![Security Scanner — 44 detectors with severity, confidence, and CWE IDs](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/security-scanner.png)

### Repo Map

Your whole repository at a glance — every source file ranked by token cost with a cost bar, plus the current branch, recent commits, and the files changed in the last commit. Click any file to jump straight to it. Refreshes on save.

![Repo Map — files ranked by token cost with branch and recent-commit context](https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/screenshots/repo-map.png)

### Game Plan

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
| **Free** | $0 | Token Waste · Repo Map · Unlimited scans · No credit card required |
| **Pro** | $9.99/mo | Everything in Free + Security · Game Plan · AI goal suggestions · Unlimited scans |
| **Annual** | $89/yr | Same as Pro · Unlimited scans · ~26% savings vs monthly |

> **Try Pro free for 7 days — no credit card.** Run **RepoScope: Start Free 7-Day Pro Trial** from the Command Palette to unlock Security and the AI Game Plan locally.

Manage billing at [reposcope.app](https://reposcope.app).

---

## Support

Questions, bugs, or feedback: **[support@reposcope.app](mailto:support@reposcope.app)**

---

Built by [NxGen Tech Solutions](https://nxgentechsolutions.com)
