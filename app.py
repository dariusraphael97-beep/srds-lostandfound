"""
SRDS Lost & Found Website
Saddle River Day School — FBLA Website Coding & Development 2025-2026
Backend: Flask (Python) + SQLite
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

    # Seed sample items if table is empty
    count = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    if count == 0:
        # Sample items with accurate specific photos, quantities, and detailed descriptions
        # Columns: name, category, description, location, date_found, photo_url, quantity, item_detail
        sample_items = [
            (
                "AirPods Pro (2nd Gen) — Left Bud",
                "Electronics",
                "Single left AirPod Pro (2nd Generation). White, fits snugly in ear. No case. Found on gym bleacher seat after 3rd period.",
                "Gymnasium — Bleachers Row C",
                "2026-02-10",
                "https://images.unsplash.com/photo-1603351154351-5e2d0600bb77?w=600&q=80",
                1,
                "Model: AirPods Pro 2nd Gen · Bud: LEFT · Case: No · Serial: Unknown"
            ),
            (
                "AirPods Pro (2nd Gen) — Right Bud",
                "Electronics",
                "Single right AirPod Pro (2nd Generation). White, slightly scuffed tip. No case. Found near the water fountains in North Hall.",
                "North Hall — Water Fountain Area",
                "2026-02-12",
                "https://images.unsplash.com/photo-1603351154351-5e2d0600bb77?w=600&q=80",
                1,
                "Model: AirPods Pro 2nd Gen · Bud: RIGHT · Case: No · Serial: Unknown"
            ),
            (
                "AirPods (3rd Gen) — Full Set in Case",
                "Electronics",
                "Full set of AirPods 3rd Generation in white MagSafe charging case. Case has a small blue sticker on the back.",
                "Library — Study Table 4",
                "2026-02-14",
                "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&q=80",
                1,
                "Model: AirPods 3rd Gen · Both buds present · Case: Yes (MagSafe) · Sticker on case"
            ),
            (
                "Blue Nike Backpack",
                "Bags & Backpacks",
                "Large blue Nike Brasilia backpack with red drawstring keychain. Contains spiral notebooks and a pencil case. Left in main hallway.",
                "Main Hallway — near Lockers B12",
                "2026-02-11",
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&q=80",
                1,
                "Brand: Nike Brasilia · Color: Blue · Contents: Notebooks, pencil case"
            ),
            (
                "TI-84 Plus CE Calculator",
                "Electronics",
                "Black Texas Instruments TI-84 Plus CE graphing calculator. Name written in marker on back: J. Morris. Found on desk after class.",
                "Math Department — Room 112",
                "2026-02-13",
                "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600&q=80",
                1,
                "Model: TI-84 Plus CE · Color: Black · Name on back: J. Morris"
            ),
            (
                "TI-84 Plus CE Calculators (×2)",
                "Electronics",
                "Two identical black TI-84 Plus CE calculators found together in a desk drawer after class. No names written on either.",
                "Science Wing — Room 204",
                "2026-02-15",
                "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=600&q=80",
                2,
                "Model: TI-84 Plus CE · Color: Black × 2 · No names written"
            ),
            (
                "Green Hydro Flask (32oz)",
                "Water Bottles",
                "32oz Hydro Flask in forest green with multiple stickers on the side including a sunflower and a mountain sticker.",
                "Library — Study Room 2",
                "2026-02-10",
                "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&q=80",
                1,
                "Brand: Hydro Flask · Size: 32oz · Color: Forest Green · Stickers: Sunflower, mountain"
            ),
            (
                "Black Champion Zip Hoodie",
                "Clothing & Apparel",
                "Black Champion zip-up hoodie, size Medium. Left on a cafeteria chair after lunch. No name inside.",
                "Cafeteria — Table Area",
                "2026-02-12",
                "https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=600&q=80",
                1,
                "Brand: Champion · Color: Black · Size: Medium · Style: Zip-up"
            ),
            (
                "Set of House Keys",
                "Keys",
                "Set of 3 keys on a silver ring with a small blue rubber keychain shaped like a star. Found near the front entrance.",
                "Front Office — Main Entrance",
                "2026-02-09",
                "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
                1,
                "Keys: 3 total · Keychain: Blue star rubber · Ring: Silver"
            ),
            (
                "Adidas Soccer Cleats (Size 10)",
                "Sports Equipment",
                "Black and white Adidas Copa soccer cleats, men's size 10. Found in a bag near the athletic field entrance after practice.",
                "Athletic Fields — Equipment Room",
                "2026-02-11",
                "https://images.unsplash.com/photo-1511886929837-354d827aae26?w=600&q=80",
                1,
                "Brand: Adidas Copa · Color: Black & White · Size: Men's 10 · Condition: Used"
            ),
            (
                "Gold Heart Charm Bracelet",
                "Jewelry & Accessories",
                "Thin gold chain bracelet with a small heart charm. Delicate clasp. Found on the gymnasium floor after morning assembly.",
                "Gymnasium — Main Floor",
                "2026-02-13",
                "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=600&q=80",
                1,
                "Material: Gold tone · Charm: Small heart · Clasp: Lobster claw · Length: ~7 inches"
            ),
            (
                "Ray-Ban Wayfarer Sunglasses",
                "Jewelry & Accessories",
                "Classic black Ray-Ban Original Wayfarer sunglasses in a black soft case. Found on the outdoor lunch bench.",
                "Outdoor Lunch Area — Bench 3",
                "2026-02-14",
                "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&q=80",
                1,
                "Brand: Ray-Ban · Model: Original Wayfarer RB2140 · Color: Black · Case: Yes"
            ),
            (
                "Grey North Face Puffer Jacket",
                "Clothing & Apparel",
                "Grey North Face Nuptse puffer jacket, size Large. Found hanging on a chair in a classroom. No name tag inside.",
                "Upper School — Room 304",
                "2026-02-15",
                "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=600&q=80",
                1,
                "Brand: The North Face · Style: Nuptse Puffer · Color: Grey · Size: Large"
            ),
            (
                "Apple MacBook USB-C Charger",
                "Electronics",
                "Apple 65W USB-C MacBook charger with white cable. No name on it. Found plugged into an outlet in the library charging station.",
                "Library — Charging Station",
                "2026-02-16",
                "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&q=80",
                1,
                "Brand: Apple · Wattage: 65W · Connector: USB-C · Cable included: Yes"
            ),
            (
                "Purple Spiral Notebook",
                "Books & Stationery",
                "Purple spiral-bound notebook, college rule. Name written inside front cover: A. Chen. Appears to contain History notes.",
                "Cafeteria — Table 7",
                "2026-02-10",
                "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=600&q=80",
                1,
                "Color: Purple · Style: Spiral · Rule: College · Name inside: A. Chen · Subject: History"
            ),
        ]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in sample_items:
            db.execute(
                """INSERT INTO items
                   (name, category, description, location, date_found, photo_url, quantity, item_detail, status, submitted)
                   VALUES (?,?,?,?,?,?,?,?,'approved',?)""",
                (*item, now)
            )
        db.commit()
    db.close()


def enrich_items(rows):
    """Add emoji; photo_url is already in the DB column. Fall back to category photo."""
    result = []
    for row in rows:
        d = dict(row)
        d["emoji"] = CATEGORY_EMOJI.get(d["category"], "📦")
        # photo_url column has external URLs; photo column has local uploads
        # If neither, fall back to category default
        if not d.get("photo_url") and not d.get("photo"):
            d["photo_url"] = CATEGORY_PHOTOS.get(d["category"])
        result.append(d)
    return result


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Routes ----------

@app.route("/")
def index():
    db = get_db()
    recent_rows = db.execute(
        "SELECT * FROM items WHERE status='approved' ORDER BY id DESC LIMIT 6"
    ).fetchall()
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
        flash("Item reported! It will appear once reviewed by an admin.", "success")
        return redirect(url_for("index"))

    return render_template("report.html")


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

        db.execute(
            "INSERT INTO claims (item_id, claimant, email, student_id, message, submitted) VALUES (?,?,?,?,?,?)",
            (item_id, claimant, email, student_id, message, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
        flash("Claim submitted! We'll contact you via email soon.", "success")
        return redirect(url_for("items"))

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


# ---------- Admin Routes ----------

ADMIN_PASSWORD = "srds2026"


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
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
    return render_template("admin.html",
        pending_items=pending_items, approved_items=approved_items,
        claimed_items=claimed_items, pending_claims=pending_claims,
        notifications=notifications)


@app.route("/admin/action", methods=["POST"])
def admin_action():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    action   = request.form.get("action")
    item_id  = request.form.get("item_id")
    claim_id = request.form.get("claim_id")
    db = get_db()

    if action == "approve_item":
        db.execute("UPDATE items SET status='approved' WHERE id=?", (item_id,))
        flash("Item approved and published.", "success")
    elif action == "reject_item":
        db.execute("DELETE FROM items WHERE id=?", (item_id,))
        flash("Item rejected and removed.", "success")
    elif action == "mark_claimed":
        db.execute("UPDATE items SET status='claimed' WHERE id=?", (item_id,))
        flash("Item marked as claimed.", "success")
    elif action == "approve_claim":
        claim = db.execute("SELECT * FROM claims WHERE id=?", (claim_id,)).fetchone()
        if claim:
            db.execute("UPDATE items SET status='claimed' WHERE id=?", (claim["item_id"],))
            db.execute("UPDATE claims SET status='approved' WHERE id=?", (claim_id,))
            flash("Claim approved. Item marked as claimed.", "success")
    elif action == "reject_claim":
        db.execute("UPDATE claims SET status='rejected' WHERE id=?", (claim_id,))
        flash("Claim rejected.", "success")

    db.commit()
    return redirect(url_for("admin_dashboard"))


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
