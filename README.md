# SRDS Lost & Found
**Saddle River Day School — FBLA Website Coding & Development 2025–2026**

A full-stack lost and found web application built from scratch for the FBLA Website Coding & Development event.

---

## Live Site
Deployed on Railway — see submission for URL.  
**Admin Demo Password:** `srds2026`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Framework | Flask 3.x |
| Database | SQLite 3 (via Python `sqlite3`) |
| Server | Gunicorn (production) |
| Hosting | Railway (cloud PaaS) |
| Frontend | Vanilla HTML5 + CSS3 + JavaScript — no frameworks |
| Fonts | Google Fonts — Inter, Cormorant Garamond, Plus Jakarta Sans |

> No Bootstrap, Tailwind, jQuery, or any UI library. All CSS and JS is original.

---

## Project Structure

```
srds-lostandfound/
├── app.py                  # All routes, DB schema, migrations, business logic
├── requirements.txt        # Python dependencies (Flask, Werkzeug, Gunicorn)
├── Procfile                # Railway startup: gunicorn app:app
├── static/
│   ├── css/style.css       # All styles — layout, animations, dark mode, responsive
│   ├── js/main.js          # Cursor, scroll reveals, counters, bookmarks, transitions
│   └── img/srds-logo.svg   # Hand-coded SVG school crest
└── templates/
    ├── base.html           # Shared nav, footer, flash messages
    ├── index.html          # Home — hero, live stats, recent items
    ├── items.html          # Browse found items — search + category filter
    ├── item_detail.html    # Single item page with photo + specs
    ├── claim.html          # Claim form with live proof-strength meter
    ├── report.html         # Report a found item (with photo upload)
    ├── lost_report.html    # Lost item report + Smart Match results
    ├── heatmap.html        # SVG campus heatmap visualization
    ├── timeline.html       # Item journey timeline (Reported → Returned)
    ├── admin_login.html    # Staff password login
    ├── admin.html          # Admin dashboard — tabbed item/claim management
    └── credits.html        # Sources & Credits (libraries, fonts, images)
```

---

## Key Original Features

### 1. Smart Match Engine — `smart_match()` in app.py
Weighted scoring algorithm matches lost reports against found items:
- Category match → +35 pts
- Location keyword overlap → up to +25 pts  
- Date range proximity → +20 pts inside range, +12 pts near range
- Name/description keyword overlap → up to +30 pts  
Returns top 5 matches with confidence % and human-readable reason pills.

### 2. Private Proof Claim System — `/claim/<id>`
Claimants describe a hidden detail only the true owner would know. A live JS meter scores proof strength (0–100) based on length + specific identifiers (serial numbers, scratches, initials, etc.). Score stored in DB, visible to admins during claim review.

### 3. Campus Heatmap — `/heatmap`
Hand-coded SVG map of SRDS campus. Hotspot dot radius scales with item count. Color: red = high, orange = medium, blue = low. Animated pulse on high-frequency zones.

### 4. Item Journey Timeline — `/timeline/<id>`
Vertical timeline: Reported → Staff Review → Claim Submitted → Returned. Events auto-logged to `item_events` table at every status change.

### 5. AirPods Variant Tracking
Multiple similar items tracked as variants under one parent (model, which bud, case included) with independent quantities.

---

## Database Schema

```sql
items         — id, name, category, description, location, date_found,
                photo, photo_url, quantity, item_detail, status, submitted

claims        — id, item_id, claimant, email, student_id, message,
                proof_detail, proof_score, status, submitted

lost_reports  — id, name, category, description, location, date_lost, contact, submitted

item_events   — id, item_id, event, detail, timestamp

item_variants — id, item_id, variant, quantity

notifications — id, email, keyword, created
```

---

## Admin Workflow

1. Visit `/admin` → password: `srds2026`
2. **Pending** — approve/reject submitted items → goes live or deleted
3. **Live** — all published items → mark as Claimed
4. **Claims** — review claimant name, grade, proof score (0–100), hidden detail → approve/reject
5. **Claimed** — archive of returned items

---

## Running Locally

```bash
pip install flask werkzeug gunicorn
python app.py
# Open http://localhost:5000
```

---

## Accessibility Highlights
- Semantic HTML5 (`<nav>`, `<main>`, `<header>`, `<section>`, `<footer>`)
- ARIA labels on all interactive elements and live regions
- Full keyboard navigation — Tab, Enter, Escape
- `Ctrl+K` global search shortcut
- WCAG 2.1 AA color contrast on all text
- Responsive: desktop → tablet → mobile with hamburger nav

---

## Sources & Credits
See the live `/credits` page for full library, font, and image attribution.

---

*All code is original. No templates or UI frameworks were used.*
