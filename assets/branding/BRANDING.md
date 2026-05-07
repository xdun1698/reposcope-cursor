# CodeWalker — Brand Assets

**Primary logo:** Dark navy background (`#0d1117`), green node-graph with interconnected circles and lines. No text. Represents the 3D code visualization concept.

---

## Source File

| File | Notes |
|------|-------|
| `New-logo-test.pdf` (parent `assets/`) | Master vector source. Use this to re-export at any size. |

---

## Exported PNGs

| File | Size | Use |
|------|------|-----|
| `codewalker-logo-master.png` | 1989×1989 | Archival master (cropped square from PDF) |
| `codewalker-logo-1024.png` | 1024×1024 | Marketing, general hi-res (e.g. Steam store if you ship that product) |
| `codewalker-logo-640.png` | 640×640 | Square marketing / social (not required for Cursor marketplace) |
| `codewalker-logo-512.png` | 512×512 | Cursor / VS Code extension icon (`package.json` / marketplace) |
| `codewalker-icon-128.png` | 128×128 | **Stripe App icon** (referenced in `stripe-app.json`) |
| `codewalker-logo-64.png` | 64×64 | Favicon, small UI uses |

Root shortcuts (in `assets/`):
- `codewalker-icon.png` → copy of the 128×128 (for Stripe App)
- `codewalker-logo.png` → copy of the 1024×1024 (general use)

---

## Where Each Logo Lives in the Codebase

| Destination | File | Status |
|-------------|------|--------|
| Stripe App | `stripe-integration/stripe-app/codewalker-icon.png` | ✅ Copied |
| Stripe App config | `stripe-integration/stripe-app/stripe-app.json` → `"icon": "codewalker-icon.png"` | ✅ Already wired |
| Cursor extension | `assets/codewalker-icon.png` (referenced from `package.json`) | Primary ship target |
| Steam / Telegram | Same PNGs can be reused if you run those channels | Optional — not part of Cursor launch |

---

## Brand Colors

| Color | Hex | Use |
|-------|-----|-----|
| Background | `#0d1117` | App dark background, README headers |
| Node green | `#4caf50` (approx) | Primary accent, buttons, highlights |
| Edge green | `#388e3c` (approx) | Secondary accent, borders |

---

## Regenerating from PDF

```bash
cd ~/Codewalker/assets
python3 - <<'EOF'
from pdf2image import convert_from_path
from PIL import Image

pages = convert_from_path("New-logo-test.pdf", dpi=300)
img = pages[0]
w, h = img.size
crop_w = int(w * 0.78)
img_cropped = img.crop((0, 0, crop_w, h))
side = min(img_cropped.size)
left = (img_cropped.width - side) // 2
top = (img_cropped.height - side) // 2
img_square = img_cropped.crop((left, top, left + side, top + side))
img_square.resize((640, 640)).save("branding/codewalker-logo-640.png")
print("Done")
EOF
```
