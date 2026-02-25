"""
SRDS Lost & Found — Web Application
=====================================
Saddle River Day School | FBLA Website Coding & Development 2025-2026

Author:  SRDS FBLA Chapter
Stack:   Python 3.12 + Flask 3.x + SQLite3 + Gunicorn + Railway
All code is original — no templates, frameworks, or generators used.

Route Map:
  GET  /                  Home page (recent items + stats)
  GET  /items             Browse all found items (search + filter)
  GET  /item/<id>         Item detail page
  GET  /claim/<id>        Claim form for a specific item
  POST /claim/<id>        Submit a claim with private proof detail
  GET  /report            Report a found item form
  POST /report            Submit a found item (photo upload handled here)
  GET  /lost              Lost item report + Smart Match form
  POST /lost              Run Smart Match, save lost report to DB
  GET  /heatmap           Campus heatmap visualization (SVG)
  GET  /timeline/<id>     Item journey timeline
  GET  /credits           Sources & Credits page
  GET  /admin             Admin login (redirects to dashboard if logged in)
  POST /admin             Process admin login
  GET  /admin/dashboard   Full admin dashboard (requires session)
  POST /admin/action      Approve/reject items and claims
  GET  /admin/logout      Clear admin session
"""

import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "srds_lost_found_rebels_2026"

UPLOAD_FOLDER = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "/tmp"), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
DATABASE = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "/tmp"), "lostandfound.db")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Category emoji map
CATEGORY_EMOJI = {
    "Clothing & Apparel":   "👕",
    "Electronics":          "📱",
    "Books & Stationery":   "📚",
    "Bags & Backpacks":     "🎒",
    "Sports Equipment":     "⚽",
    "Jewelry & Accessories":"💍",
    "Keys":                 "🔑",
    "Water Bottles":        "💧",
    "Other":                "📦",
}

# Curated Unsplash placeholder images by category (royalty-free)
CATEGORY_PHOTOS = {
    "Electronics":          "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&q=80",
    "Bags & Backpacks":     "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=600&q=80",
    "Clothing & Apparel":   "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=600&q=80",
    "Books & Stationery":   "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&q=80",
    "Water Bottles":        "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&q=80",
    "Keys":                 "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
    "Sports Equipment":     "https://images.unsplash.com/photo-1530549387789-4c1017266635?w=600&q=80",
    "Jewelry & Accessories":"https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=600&q=80",
    "Other":                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80",
}


# ─── Database helpers ─────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db: db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT    NOT NULL,
            location    TEXT    NOT NULL,
            date_found  TEXT    NOT NULL,
            photo       TEXT    DEFAULT NULL,
            photo_url   TEXT    DEFAULT NULL,
            quantity    INTEGER DEFAULT 1,
            item_detail TEXT    DEFAULT NULL,
            status      TEXT    DEFAULT 'pending',
            submitted   TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS claims (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id     INTEGER NOT NULL,
            claimant    TEXT    NOT NULL,
            email       TEXT    NOT NULL,
            student_id  TEXT    NOT NULL,
            message     TEXT,
            submitted   TEXT    NOT NULL,
            status      TEXT    DEFAULT 'pending',
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    NOT NULL,
            keyword     TEXT    NOT NULL,
            created     TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lost_reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT    NOT NULL,
            location    TEXT    NOT NULL,
            date_lost   TEXT    NOT NULL,
            contact     TEXT    NOT NULL,
            submitted   TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS item_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id     INTEGER NOT NULL,
            event       TEXT    NOT NULL,
            detail      TEXT    DEFAULT NULL,
            timestamp   TEXT    NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS item_variants (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id     INTEGER NOT NULL,
            variant     TEXT    NOT NULL,
            quantity    INTEGER DEFAULT 1,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );
    """)
    db.commit()

    # Run migrations for existing databases (adds new columns if missing)
    existing_cols = [r[1] for r in db.execute("PRAGMA table_info(items)").fetchall()]
    migrations = [
        ("photo_url",    "ALTER TABLE items ADD COLUMN photo_url   TEXT    DEFAULT NULL"),
        ("quantity",     "ALTER TABLE items ADD COLUMN quantity     INTEGER DEFAULT 1"),
        ("item_detail",  "ALTER TABLE items ADD COLUMN item_detail  TEXT    DEFAULT NULL"),
    ]
    for col, sql in migrations:
        if col not in existing_cols:
            db.execute(sql)
    db.commit()

    # Create item_variants table if missing
    db.execute("""CREATE TABLE IF NOT EXISTS item_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        variant TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (item_id) REFERENCES items(id)
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS lost_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, category TEXT NOT NULL,
        description TEXT NOT NULL, location TEXT NOT NULL,
        date_lost TEXT NOT NULL, contact TEXT NOT NULL,
        submitted TEXT NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS item_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        event TEXT NOT NULL,
        detail TEXT DEFAULT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items(id)
    )""")
    # Add proof_detail to claims if missing
    claim_cols = [r[1] for r in db.execute("PRAGMA table_info(claims)").fetchall()]
    if "proof_detail" not in claim_cols:
        db.execute("ALTER TABLE claims ADD COLUMN proof_detail TEXT DEFAULT NULL")
    if "proof_score" not in claim_cols:
        db.execute("ALTER TABLE claims ADD COLUMN proof_score INTEGER DEFAULT 0")
    # Strip legacy "url:" prefix from any existing photo_url values
    db.execute("UPDATE items SET photo_url = SUBSTR(photo_url, 5) WHERE photo_url LIKE 'url:%'")
    db.commit()

    # Seed sample items if table is empty
    count = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    if count == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        items_data = [
            ("Apple AirPods",
             "Electronics",
             "Multiple Apple AirPods found across campus. Click View Details to see each variant — model, which bud(s), case included, and how many of each are still unclaimed.",
             "North Hall — Multiple Areas",
             "2026-02-10",
             "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&q=80",
             5,
             "Brand: Apple · Multiple models · See variants below"),

            ("Blue Nike Backpack",
             "Bags & Backpacks",
             "Large blue Nike Brasilia backpack with a red drawstring keychain. Contains spiral notebooks and a pencil case.",
             "Main Hallway — near Lockers B12",
             "2026-02-11",
             "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80",
             1, "Brand: Nike Brasilia · Color: Blue"),

            ("TI-84 Plus CE Calculator",
             "Electronics",
             "Black Texas Instruments TI-84 Plus CE graphing calculator. Name written in marker on back: J. Morris.",
             "Math Department — Room 112",
             "2026-02-13",
             "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600&q=80",
             2, "Model: TI-84 Plus CE · Color: Black"),

            ("Green Hydro Flask (32oz)",
             "Water Bottles",
             "32oz Hydro Flask in forest green with stickers on the side — sunflower and mountain.",
             "Library — Study Room 2",
             "2026-02-10",
             "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&q=80",
             1, "Brand: Hydro Flask · Size: 32oz · Color: Forest Green"),

            ("Black Champion Zip Hoodie",
             "Clothing & Apparel",
             "Black Champion zip-up hoodie, size Medium. Left on a cafeteria chair after lunch.",
             "Cafeteria — Table Area",
             "2026-02-12",
             "https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=600&q=80",
             1, "Brand: Champion · Color: Black · Size: Medium"),

            ("Set of House Keys",
             "Keys",
             "Set of 3 keys on a silver ring with a small blue star-shaped rubber keychain.",
             "Front Office — Main Entrance",
             "2026-02-09",
             "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
             1, "Keys: 3 total · Keychain: Blue star"),

            ("Adidas Soccer Cleats",
             "Sports Equipment",
             "Black and white Adidas Copa soccer cleats, men's size 10. Found near equipment room.",
             "Athletic Fields — Equipment Room",
             "2026-02-11",
             "https://images.unsplash.com/photo-1511886929837-354d827aae26?w=600&q=80",
             1, "Brand: Adidas Copa · Size: Men's 10"),

            ("Gold Heart Charm Bracelet",
             "Jewelry & Accessories",
             "Thin gold chain bracelet with a small heart charm. Found on the gymnasium floor.",
             "Gymnasium — Main Floor",
             "2026-02-13",
             "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=600&q=80",
             1, "Material: Gold tone · Charm: Heart"),

            ("Ray-Ban Wayfarer Sunglasses",
             "Jewelry & Accessories",
             "Classic black Ray-Ban Original Wayfarer sunglasses in a soft case.",
             "Outdoor Lunch Area — Bench 3",
             "2026-02-14",
             "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&q=80",
             1, "Brand: Ray-Ban · Model: Wayfarer RB2140"),

            ("Grey North Face Puffer Jacket",
             "Clothing & Apparel",
             "Grey North Face Nuptse puffer jacket, size Large. Found hanging on a chair.",
             "Upper School — Room 304",
             "2026-02-15",
             "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80",
             1, "Brand: The North Face · Style: Nuptse · Size: Large"),

            ("Apple MacBook USB-C Charger",
             "Electronics",
             "Apple 65W USB-C MacBook charger with white cable. Found plugged in at the library.",
             "Library — Charging Station",
             "2026-02-16",
             "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&q=80",
             1, "Brand: Apple · Wattage: 65W · USB-C"),

            ("Purple Spiral Notebook",
             "Books & Stationery",
             "Purple spiral notebook, college ruled. Name inside: A. Chen. History notes throughout.",
             "Cafeteria — Table 7",
             "2026-02-10",
             "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=600&q=80",
             1, "Color: Purple · Ruled: College · Name: A. Chen"),
        ]

        airpods_id = None
        for row in items_data:
            name, cat, desc, loc, date, photo, qty, detail = row
            cur = db.execute(
                "INSERT INTO items (name, category, description, location, date_found, photo_url, quantity, item_detail, status, submitted) VALUES (?,?,?,?,?,?,?,?,'approved',?)",
                (name, cat, desc, loc, date, photo, qty, detail, now)
            )
            if name == "Apple AirPods":
                airpods_id = cur.lastrowid

        if airpods_id:
            variants = [
                ("AirPods Pro 2nd Gen — Left bud only, no case",   1),
                ("AirPods Pro 2nd Gen — Right bud only, no case",  1),
                ("AirPods Pro 2nd Gen — Both buds, no case",       1),
                ("AirPods 3rd Gen — Both buds + MagSafe case",     1),
                ("AirPods 2nd Gen — Left bud only, no case",       1),
            ]
            for variant, qty in variants:
                db.execute(
                    "INSERT INTO item_variants (item_id, variant, quantity) VALUES (?,?,?)",
                    (airpods_id, variant, qty)
                )

        # Seed timeline events for all items
        all_items = db.execute("SELECT id, submitted, date_found, name FROM items").fetchall()
        for it in all_items:
            db.execute("INSERT INTO item_events (item_id, event, detail, timestamp) VALUES (?,?,?,?)",
                (it["id"], "reported", f"Item reported as found at campus", it["submitted"]))
            db.execute("INSERT INTO item_events (item_id, event, detail, timestamp) VALUES (?,?,?,?)",
                (it["id"], "approved", "Item reviewed and approved by staff", it["submitted"]))

        db.commit()
    db.close()

# ─────────────────────────────────────────────
# SMART MATCH ENGINE
# Scores found items against a lost-item query
# using category, location, keywords, date range
# ─────────────────────────────────────────────
import re as _re

# ─── Smart Match Engine ───────────────────────────────────────────────────
# Scores every approved found item against a lost-item query.
# Returns top 5 results with a 0-100 confidence score and reason list.

def smart_match(name, category, description, location, date_lost, db, date_to=None):
    """Return top matches from found items with confidence scores and reasons.
    date_lost = start of range (or exact date), date_to = end of range (optional).
    """
    query_words = set(_re.sub(r"[^a-z0-9 ]", "", (name + " " + description).lower()).split())
    stop_words  = {"a","an","the","is","in","at","of","and","or","it","i","my","was","with","found","lost","have"}
    query_words -= stop_words

    rows = db.execute(
        "SELECT * FROM items WHERE status='approved' ORDER BY id DESC"
    ).fetchall()

    results = []
    for row in rows:
        score   = 0
        reasons = []
        d       = dict(row)

        # Category match (strong signal)
        if d["category"] == category:
            score += 35
            reasons.append("Same category")

        # Location similarity
        qloc = location.lower()
        iloc = d["location"].lower()
        loc_words = set(qloc.split()) & set(iloc.split()) - {"the","—","-","room","hall","area"}
        if loc_words:
            score += min(25, len(loc_words) * 12)
            reasons.append(f"Nearby location ({', '.join(list(loc_words)[:2])})")

        # Date proximity — supports single date or range
        try:
            from datetime import datetime as _dt
            df  = _dt.strptime(d["date_found"], "%Y-%m-%d")
            dl_start = _dt.strptime(date_lost, "%Y-%m-%d")
            dl_end   = _dt.strptime(date_to, "%Y-%m-%d") if date_to else dl_start
            # Check if found date falls within lost range (with 3-day buffer each side)
            from datetime import timedelta
            buffered_start = dl_start - timedelta(days=3)
            buffered_end   = dl_end   + timedelta(days=3)
            if buffered_start <= df <= buffered_end:
                # Found date is inside the lost range
                if dl_start <= df <= dl_end:
                    score += 20; reasons.append("Found within your date range")
                else:
                    score += 12; reasons.append("Found near your date range")
            else:
                # Outside range — smaller score based on nearest edge
                nearest = min(abs((df - dl_start).days), abs((df - dl_end).days))
                if nearest <= 7:
                    score += 6; reasons.append(f"Found ~{nearest}d from your range")
        except:
            pass

        # Keyword overlap in name + description
        item_words = set(_re.sub(r"[^a-z0-9 ]", "",
            (d["name"] + " " + d["description"] + " " + (d["item_detail"] or "")).lower()
        ).split()) - stop_words
        overlap = query_words & item_words
        if overlap:
            score += min(30, len(overlap) * 8)
            reasons.append(f"Keyword match: {', '.join(list(overlap)[:3])}")

        if score >= 20:
            results.append({
                "item":       d,
                "score":      min(score, 99),
                "confidence": "High" if score >= 65 else "Medium" if score >= 40 else "Low",
                "reasons":    reasons,
                "photo_url":  d.get("photo_url"),
                "emoji":      CATEGORY_EMOJI.get(d["category"], "📦"),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]



# ─── Item enrichment ──────────────────────────────────────────────────────

def enrich_items(rows):
    """Add emoji; strip url: prefix from photo_url. Fall back to category photo."""
    result = []
    for row in rows:
        d = dict(row)
        d["emoji"] = CATEGORY_EMOJI.get(d["category"], "📦")
        # Strip legacy "url:" prefix if present
        if d.get("photo_url") and str(d["photo_url"]).startswith("url:"):
            d["photo_url"] = d["photo_url"][4:]
        # Fall back to category default if no photo at all
        if not d.get("photo_url") and not d.get("photo"):
            d["photo_url"] = CATEGORY_PHOTOS.get(d["category"])
        result.append(d)
    return result


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Routes ───────────────────────────────────────────────────────────────

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve user-uploaded item photos from the dynamic upload folder."""
    from flask import send_from_directory
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/")
def index():
    db = get_db()
    recent_rows = db.execute("SELECT * FROM items WHERE status='approved' ORDER BY id DESC LIMIT 6").fetchall()
    total   = db.execute("SELECT COUNT(*) FROM items WHERE status='approved'").fetchone()[0]
    claimed = db.execute("SELECT COUNT(*) FROM items WHERE status='claimed'").fetchone()[0]
    return render_template("index.html", recent=enrich_items(recent_rows), total=total, claimed=claimed)


@app.route("/items")
def items():
    db = get_db()
    search   = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query  = "SELECT * FROM items WHERE status='approved'"
    params = []

    if search:
        query  += " AND (name LIKE ? OR description LIKE ? OR location LIKE ?)"
        like    = f"%{search}%"
        params += [like, like, like]

    if category:
        query  += " AND category=?"
        params.append(category)

    query += " ORDER BY id DESC"
    rows = db.execute(query, params).fetchall()

    categories = [r["category"] for r in db.execute(
        "SELECT DISTINCT category FROM items WHERE status='approved' ORDER BY category"
    ).fetchall()]

    return render_template("items.html", items=enrich_items(rows), search=search,
                           category=category, categories=categories)


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        category    = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location    = request.form.get("location", "").strip()
        date_found  = request.form.get("date_found", "").strip()

        if not all([name, category, description, location, date_found]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("report"))

        photo_filename = None
        if "photo" in request.files:
            file = request.files["photo"]
            if file and file.filename and allowed_file(file.filename):
                photo_filename = secure_filename(
                    f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                )
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_filename))

        db = get_db()
        db.execute(
            """INSERT INTO items
               (name, category, description, location, date_found, photo, quantity, item_detail, submitted)
               VALUES (?,?,?,?,?,?,1,NULL,?)""",
            (name, category, description, location, date_found, photo_filename,
             datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
        new_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        # Log the event
        db.execute("INSERT INTO item_events (item_id, event, detail, timestamp) VALUES (?,?,?,?)",
            (new_id, "reported", "Item reported as found at campus", datetime.now().strftime("%Y-%m-%d %H:%M")))
        db.commit()
        return redirect(url_for("report_success", item_id=new_id))

    return render_template("report.html")


@app.route("/report/success/<int:item_id>")
def report_success(item_id):
    """Confirmation page shown after reporting a found item — shows admin review status."""
    db  = get_db()
    row = db.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        return redirect(url_for("index"))
    item = enrich_items([row])[0]
    is_admin = session.get("admin")
    return render_template("report_success.html", item=item, is_admin=is_admin)


@app.route("/item/<int:item_id>")
def item_detail(item_id):
    db = get_db()
    row = db.execute("SELECT * FROM items WHERE id=? AND status='approved'", (item_id,)).fetchone()
    if not row:
        flash("Item not found.", "error")
        return redirect(url_for("items"))
    item = enrich_items([row])[0]
    variants = db.execute(
        "SELECT * FROM item_variants WHERE item_id=? ORDER BY id", (item_id,)
    ).fetchall()
    return render_template("item_detail.html", item=item, variants=variants)


@app.route("/claim/<int:item_id>", methods=["GET", "POST"])
def claim(item_id):
    db   = get_db()
    row  = db.execute("SELECT * FROM items WHERE id=? AND status='approved'", (item_id,)).fetchone()
    if not row:
        flash("Item not found or unavailable.", "error")
        return redirect(url_for("items"))

    item = enrich_items([row])[0]

    if request.method == "POST":
        claimant   = request.form.get("claimant", "").strip()
        email      = request.form.get("email", "").strip()
        student_id = request.form.get("student_id", "").strip()
        message    = request.form.get("message", "").strip()

        if not all([claimant, email, student_id]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("claim", item_id=item_id))

        proof_detail = request.form.get("proof_detail", "").strip()
        # Calculate proof score: longer + more specific = higher
        proof_score = 0
        if proof_detail:
            proof_score += min(50, len(proof_detail) // 3)
            specific_keywords = ["serial","number","sticker","scratch","crack","initials","color","broken","dent","tag","wrote","name","code"]
            for kw in specific_keywords:
                if kw in proof_detail.lower():
                    proof_score += 8
            proof_score = min(proof_score, 100)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            "INSERT INTO claims (item_id, claimant, email, student_id, message, proof_detail, proof_score, submitted) VALUES (?,?,?,?,?,?,?,?)",
            (item_id, claimant, email, student_id, message, proof_detail, proof_score, now_str),
        )
        # Log timeline event
        db.execute(
            "INSERT INTO item_events (item_id, event, detail, timestamp) VALUES (?,?,?,?)",
            (item_id, "claim_submitted", f"Claim by {claimant} (proof score: {proof_score})", now_str)
        )
        db.commit()
        flash("Claim submitted! We'll contact you via email soon.", "success")
        return redirect(url_for("timeline", item_id=item_id))

    return render_template("claim.html", item=item)


@app.route("/notify", methods=["POST"])
def notify():
    email   = request.form.get("email", "").strip()
    keyword = request.form.get("keyword", "").strip()
    if email and keyword:
        db = get_db()
        db.execute(
            "INSERT INTO notifications (email, keyword, created) VALUES (?,?,?)",
            (email, keyword, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        db.commit()
        flash(f"We'll email {email} when a '{keyword}' item is posted!", "success")
    else:
        flash("Please enter both your email and a keyword.", "error")
    return redirect(url_for("items"))



@app.route("/lost", methods=["GET", "POST"])
def lost_report():
    """Page to report a lost item — triggers smart match suggestions."""
    matches = []
    form_data = {}
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        category    = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location    = request.form.get("location", "").strip()
        date_from   = request.form.get("date_from", "").strip()
        date_to     = request.form.get("date_to",   "").strip()
        date_lost   = date_from  # keep compatibility — use start of range
        contact     = request.form.get("contact", "").strip()
        form_data   = dict(request.form)

        if not all([name, category, description, location, date_from, date_to, contact]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("lost_report"))

        db = get_db()
        db.execute(
            "INSERT INTO lost_reports (name, category, description, location, date_lost, contact, submitted) VALUES (?,?,?,?,?,?,?)",
            (name, category, description, location, f"{date_from} to {date_to}", contact,
             datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        db.commit()

        # Run smart match
        matches = smart_match(name, category, description, location, date_lost, db, date_to=date_to)
        return render_template("lost_report.html", matches=matches, form_data=form_data, submitted=True)

    return render_template("lost_report.html", matches=[], form_data={}, submitted=False)


@app.route("/heatmap")
def heatmap():
    """Campus heatmap — item counts by location."""
    db   = get_db()
    rows = db.execute(
        "SELECT location, category, COUNT(*) as count FROM items WHERE status='approved' GROUP BY location, category ORDER BY count DESC"
    ).fetchall()
    # Build location → counts dict
    from collections import defaultdict
    loc_data = defaultdict(lambda: {"total": 0, "categories": defaultdict(int)})
    for r in rows:
        loc_data[r["location"]]["total"]  += r["count"]
        loc_data[r["location"]]["categories"][r["category"]] += r["count"]
    return render_template("heatmap.html", loc_data=dict(loc_data))


@app.route("/timeline/<int:item_id>")
def timeline(item_id):
    db  = get_db()
    row = db.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        flash("Item not found.", "error")
        return redirect(url_for("items"))
    item   = enrich_items([row])[0]
    events = db.execute(
        "SELECT * FROM item_events WHERE item_id=? ORDER BY timestamp", (item_id,)
    ).fetchall()
    claims = db.execute(
        "SELECT * FROM claims WHERE item_id=? ORDER BY submitted", (item_id,)
    ).fetchall()
    return render_template("timeline.html", item=item, events=events, claims=claims)




# ─── SPA JSON APIs ────────────────────────────────────────────────────────────

@app.route("/api/items")
def api_items():
    db       = get_db()
    search   = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query    = "SELECT * FROM items WHERE status='approved'"
    params   = []
    if search:
        query += " AND (name LIKE ? OR description LIKE ? OR location LIKE ?)"
        params += [f"%{search}%"] * 3
    if category:
        query += " AND category=?"
        params.append(category)
    query += " ORDER BY id DESC LIMIT 40"
    rows  = db.execute(query, params).fetchall()
    items = enrich_items(rows)
    # Attach variant counts for AirPods-style items
    for item in items:
        variants = db.execute(
            "SELECT * FROM item_variants WHERE item_id=?", (item["id"],)
        ).fetchall()
        item["variants"] = [dict(v) for v in variants]
    return jsonify(items)

@app.route("/api/item/<int:item_id>")
def api_item(item_id):
    db  = get_db()
    row = db.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    item = enrich_items([row])[0]
    variants = db.execute("SELECT * FROM item_variants WHERE item_id=? ORDER BY id", (item_id,)).fetchall()
    item["variants"] = [dict(v) for v in variants]
    events   = db.execute("SELECT * FROM item_events WHERE item_id=? ORDER BY timestamp", (item_id,)).fetchall()
    claims   = db.execute("SELECT * FROM claims WHERE item_id=? ORDER BY submitted", (item_id,)).fetchall()
    item["events"] = [dict(e) for e in events]
    item["claim_count"] = len(claims)
    return jsonify(item)

@app.route("/api/smart_match", methods=["POST"])
def api_smart_match():
    data     = request.get_json() or {}
    name     = data.get("name", "")
    category = data.get("category", "")
    desc     = data.get("description", "")
    location = data.get("location", "")
    date_from = data.get("date_from") or data.get("date_lost", datetime.now().strftime("%Y-%m-%d"))
    date_to   = data.get("date_to")   or date_from
    db        = get_db()
    matches   = smart_match(name, category, desc, location, date_from, db, date_to=date_to)
    return jsonify(matches)

@app.route("/api/claim", methods=["POST"])
def api_claim():
    data        = request.get_json() or {}
    item_id     = data.get("item_id")
    claimant    = data.get("claimant", "").strip()
    email       = data.get("email", "").strip()
    student_id  = data.get("student_id", "").strip()
    proof_detail= data.get("proof_detail", "").strip()
    message     = data.get("message", "").strip()

    if not all([item_id, claimant, email, student_id, proof_detail]):
        return jsonify({"error": "Missing required fields"}), 400

    keywords = ["serial","number","sticker","scratch","crack","initials","broken",
                "dent","tag","wrote","name","code","charm","inside","pocket",
                "keychain","sharpie","marker","missing","chipped","strap","digits","model","color"]
    proof_score = min(40, len(proof_detail) // 3)
    for kw in keywords:
        if kw in proof_detail.lower(): proof_score += 8
    proof_score = min(proof_score, 100)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    db = get_db()
    db.execute(
        "INSERT INTO claims (item_id, claimant, email, student_id, message, proof_detail, proof_score, submitted) VALUES (?,?,?,?,?,?,?,?)",
        (item_id, claimant, email, student_id, message, proof_detail, proof_score, now_str)
    )
    db.execute(
        "INSERT INTO item_events (item_id, event, detail, timestamp) VALUES (?,?,?,?)",
        (item_id, "claim_submitted", f"Claim by {claimant} (proof score: {proof_score})", now_str)
    )
    db.commit()
    return jsonify({"success": True, "proof_score": proof_score})

@app.route("/api/lost_report", methods=["POST"])
def api_lost_report():
    data = request.get_json() or {}
    required = ["name","category","description","location","date_lost","contact"]
    if not all(data.get(k,"").strip() for k in required):
        return jsonify({"error": "Missing fields"}), 400
    db = get_db()
    db.execute(
        "INSERT INTO lost_reports (name, category, description, location, date_lost, contact, submitted) VALUES (?,?,?,?,?,?,?)",
        (data["name"], data["category"], data["description"], data["location"],
         data.get("date_lost",""), data["contact"], datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    db.commit()
    matches = smart_match(data["name"], data["category"], data["description"],
                          data["location"], data["date_lost"], db)
    return jsonify({"success": True, "matches": matches})

@app.route("/api/heatmap")
def api_heatmap():
    db   = get_db()
    rows = db.execute(
        "SELECT location, category, COUNT(*) as count FROM items WHERE status='approved' GROUP BY location, category"
    ).fetchall()
    from collections import defaultdict
    loc_data = defaultdict(lambda: {"total": 0, "categories": {}})
    for r in rows:
        loc_data[r["location"]]["total"] += r["count"]
        loc_data[r["location"]]["categories"][r["category"]] = r["count"]
    return jsonify(dict(loc_data))


@app.route("/credits")
def credits():
    return render_template("credits.html")


# ─── Admin Routes ─────────────────────────────────────────────────────────

ADMIN_PASSWORD = "srds2026"


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            next_url = session.pop("after_login", None)
            return redirect(next_url or url_for("admin_dashboard"))
        flash("Incorrect password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        # Remember where they were trying to go
        session["after_login"] = request.url
        return redirect(url_for("admin_login"))
    db = get_db()
    pending_items  = enrich_items(db.execute("SELECT * FROM items WHERE status='pending'  ORDER BY id DESC").fetchall())
    approved_items = enrich_items(db.execute("SELECT * FROM items WHERE status='approved' ORDER BY id DESC").fetchall())
    claimed_items  = enrich_items(db.execute("SELECT * FROM items WHERE status='claimed'  ORDER BY id DESC").fetchall())
    pending_claims = db.execute("""
        SELECT claims.*, items.name AS item_name
        FROM claims JOIN items ON claims.item_id = items.id
        WHERE claims.status='pending' ORDER BY claims.id DESC
    """).fetchall()
    notifications = db.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
    # active_tab lets the page auto-open the right tab (e.g. "pending" after a new report)
    active_tab = request.args.get("tab", "pending")
    return render_template("admin.html",
        pending_items=pending_items, approved_items=approved_items,
        claimed_items=claimed_items, pending_claims=pending_claims,
        notifications=notifications, active_tab=active_tab)


@app.route("/admin/action", methods=["POST"])
def admin_action():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    action   = request.form.get("action")
    item_id  = request.form.get("item_id")
    claim_id = request.form.get("claim_id")
    db = get_db()

    tab = "pending"  # default redirect tab
    if action == "approve_item":
        db.execute("UPDATE items SET status='approved' WHERE id=?", (item_id,))
        db.execute("INSERT INTO item_events (item_id, event, detail, timestamp) VALUES (?,?,?,?)",
            (item_id, "approved", "Item approved and published by admin", datetime.now().strftime("%Y-%m-%d %H:%M")))
        flash("Item approved and is now live!", "success")
        tab = "approved"  # jump to Live tab so judges see it appeared
    elif action == "reject_item":
        db.execute("DELETE FROM items WHERE id=?", (item_id,))
        flash("Item rejected and removed.", "success")
        tab = "pending"
    elif action == "mark_claimed":
        db.execute("UPDATE items SET status='claimed' WHERE id=?", (item_id,))
        db.execute("INSERT INTO item_events (item_id, event, detail, timestamp) VALUES (?,?,?,?)",
            (item_id, "returned", "Item marked as returned to owner", datetime.now().strftime("%Y-%m-%d %H:%M")))
        flash("Item marked as returned to owner.", "success")
        tab = "claimed"
    elif action == "approve_claim":
        claim = db.execute("SELECT * FROM claims WHERE id=?", (claim_id,)).fetchone()
        if claim:
            db.execute("UPDATE items SET status='claimed' WHERE id=?", (claim["item_id"],))
            db.execute("UPDATE claims SET status='approved' WHERE id=?", (claim_id,))
            flash("Claim approved — item marked as returned!", "success")
        tab = "claimed"
    elif action == "reject_claim":
        db.execute("UPDATE claims SET status='rejected' WHERE id=?", (claim_id,))
        flash("Claim rejected.", "success")
        tab = "claims"

    db.commit()
    return redirect(url_for("admin_dashboard", tab=tab))


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))


# ---------- API ----------

@app.route("/api/search")
def api_search():
    db   = get_db()
    q    = request.args.get("q", "").strip()
    like = f"%{q}%"
    rows = db.execute(
        """SELECT id, name, category, location, date_found FROM items
           WHERE status='approved' AND (name LIKE ? OR description LIKE ? OR location LIKE ?)
           ORDER BY id DESC LIMIT 10""",
        (like, like, like)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# Initialize DB on startup (works on Railway too)
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
