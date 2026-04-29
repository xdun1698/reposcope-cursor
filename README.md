# CodeWalker — Cursor Plugin

<p align="center">
  <img src="assets/codewalker-icon.png" alt="CodeWalker" width="128"/>
</p>

<p align="center">
  <strong>Token waste detection, security scanning, repo mapping, and game plan tracking — right inside Cursor.</strong>
</p>

<p align="center">
  <a href="https://marketplace.visualstudio.com/items?itemName=nxgentech.codewalker"><img src="https://img.shields.io/badge/VS%20Code-Extension-007ACC?logo=visualstudiocode&logoColor=white" alt="VS Code"/></a>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License"/>
</p>

---

## What is CodeWalker?

CodeWalker is a developer productivity plugin for [Cursor](https://cursor.com) that helps you understand large codebases, eliminate LLM token waste, and catch security issues before they ship.

### Token Waste Detection

See exactly which files eat your LLM context budget. BPE-accurate token counts per file let you prune intelligently before sending code to any AI model — saving money and improving output quality.

### Security Scanning

Real-time vulnerability detection: hardcoded secrets, injection risks, dependency issues. Findings are color-coded by severity with one-click fix suggestions.

### Repo Map

Live interactive map of your repository — file tree with token density, import graph, and Cursor session history. Click any node to jump to the file.

### Game Plan

AI-powered goal suggestions based on your repo analysis. Track progress, mark goals complete, and use "Fix with Cursor" to resolve issues directly in the editor.

---

## Install

### Cursor Marketplace

Search **"CodeWalker"** in the Cursor plugin marketplace, or install the local plugin:

```bash
# Clone into Cursor's local plugins directory
git clone https://github.com/xdun1698/codewalker-cursor.git ~/.cursor/plugins/local/codewalker
```

Then reload Cursor (Command Palette → **Developer: Reload Window**).

### VS Code / Cursor Extension

```bash
ext install nxgentech.codewalker
```

Or search **"CodeWalker"** in the Extensions sidebar.

---

## Plugin Structure

```
.cursor-plugin/plugin.json   Plugin manifest (hooks, skills, sidebar tabs)
skills/                       Python analysis scripts (token audit, vuln scan, repo trace, game plan)
commands/                     Agent commands (goal suggestions)
assets/                       Icons and branding
```

---

## Pricing

| Plan | Price | Included |
|------|-------|----------|
| **Free** | $0 | 3 analyses/day, basic graph view |
| **Pro** | $9.99/mo | Unlimited analyses · Token Waste · Security · Repo Map · Game Plan · All future features |
| **Annual** | $89/yr | Everything in Pro, ~26% savings |
| **Team** | $9.99/mo per user | Everything in Pro · Multi-seat · Shared history · Webhook alerts |

Manage billing at [nxgentechsolutions.com/billing](https://nxgentechsolutions.com/billing).

---

## Support

Questions, bugs, or feedback: **[support@nxgentechsolutions.com](mailto:support@nxgentechsolutions.com)**

---

<p align="center">
  Built by <a href="https://nxgentechsolutions.com">NxGen Tech Solutions</a>
</p>
