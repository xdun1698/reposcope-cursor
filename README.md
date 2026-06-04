# RepoScope — Cursor Plugin

<p align="center">
  <img src="https://open-vsx.org/api/nxgentech/reposcope-ai/latest/file/reposcope-icon.png" alt="RepoScope radar logo" width="128"/>
</p>

<p align="center">
  <strong>See your code. Know its cost. Ship smarter.</strong><br/>
  AI Cost Intelligence — token waste, security, 3D repo map, and persistent AI context, right inside Cursor.
</p>

<p align="center">
  <a href="vscode:extension/nxgentech.reposcope-ai"><img src="https://img.shields.io/badge/Install-VS%20Code%20%2F%20Cursor-007ACC?logo=visualstudiocode&logoColor=white" alt="Install in VS Code / Cursor"/></a>
  <a href="https://open-vsx.org/extension/nxgentech/reposcope-ai"><img src="https://img.shields.io/badge/OpenVSX-Registry-C160EF?logo=eclipse&logoColor=white" alt="OpenVSX"/></a>
  <a href="https://cursor.com/marketplace"><img src="https://img.shields.io/badge/Cursor-Marketplace-000000?logo=cursor&logoColor=white" alt="Cursor Marketplace"/></a>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License"/>
</p>

---

## What is RepoScope?

RepoScope is a developer productivity plugin for [Cursor](https://cursor.com) that helps you understand large codebases, eliminate LLM token waste, and catch security issues before they ship.

### Token Waste Detection

See exactly which files eat your LLM context budget. BPE-accurate token counts per file let you prune intelligently before sending code to any AI model — saving money and improving output quality.

### Security Scanning

Real-time vulnerability detection: hardcoded secrets, injection risks, dependency issues. Findings are color-coded by severity with one-click fix suggestions.

### 3D Repo Map

Live interactive map of your repository — file tree with token density, import graph, and Cursor session history. Click any node to jump to the file.

### Game Plan

AI-powered goal suggestions based on your repo analysis. Track progress, mark goals complete, and use "Fix with Cursor" to resolve issues directly in the editor.

---

## Install

### One-click (Cursor / VS Code)

Click the **Install** badge above or paste into the Command Palette (`Cmd+Shift+P`):

```
ext install nxgentech.reposcope-ai
```

The extension auto-registers the bundled Cursor plugin — hooks, skills, and commands activate immediately on any repo.

### Cursor Plugin Marketplace

Search **"RepoScope"** in the Cursor plugin marketplace (`Cmd+Shift+P` -> `Cursor: Open Plugin Marketplace`).

### One-command install (alternative)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/xdun1698/reposcope-cursor/main/scripts/install.sh)
```

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
| **Free** | $0 | 3 analyses/day · Token Waste · 3D Repo Map · No credit card required |
| **Pro** | $9.99/mo | 500K repo-token pool/mo · Everything in Free + Security · Game Plan · AI goal suggestions |
| **Annual** | $89/yr | Same as Pro · ~26% savings vs monthly |

> **Try Pro free for 7 days — no credit card.** Run **RepoScope: Start Free 7-Day Pro Trial** from the Command Palette to unlock Security and the AI Game Plan locally.

Manage billing at [reposcope.app](https://reposcope.app).

---

## Support

Questions, bugs, or feedback: **[support@reposcope.app](mailto:support@reposcope.app)**

---

<p align="center">
  Built by <a href="https://nxgentechsolutions.com">NxGen Tech Solutions</a>
</p>
