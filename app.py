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

    # Seed sample items if table is empty
    count = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    if count == 0:
        sample_items = [
            ("Blue Nike Backpack",       "Bags & Backpacks",     "Large blue Nike backpack with a red keychain. Several notebooks inside.",              "Main Hallway — near Lockers",   "2025-01-15"),
            ("Apple AirPods Pro",        "Electronics",          "White AirPods Pro in a white charging case. Case has a small scratch on the lid.",     "Gym Bleachers",                 "2025-01-16"),
            ("Green Hydroflask",         "Water Bottles",        "32oz Hydroflask in forest green with stickers on the side.",                           "Library Study Room 2",          "2025-01-17"),
            ("Black Champion Hoodie",    "Clothing & Apparel",   "Black Champion zip-up hoodie, size Medium. Left in the cafeteria after lunch.",        "Cafeteria",                     "2025-01-18"),
            ("Set of House Keys",        "Keys",                 "3 keys on a silver ring with a small blue rubber keychain.",                           "Front Office Entrance",         "2025-01-19"),
            ("TI-84 Calculator",         "Electronics",          "TI-84 Plus CE graphing calculator. Name on back in permanent marker: J. Morris.",      "Math Department Hallway",       "2025-01-20"),
            ("Soccer Cleats",            "Sports Equipment",     "Black and white Adidas soccer cleats, size 10. Found near the athletic fields.",       "Athletic Fields — Equipment Rm","2025-01-21"),
            ("Gold Bracelet",            "Jewelry & Accessories","Thin gold chain bracelet with a small heart charm. Found on the gym floor.",           "Gymnasium",                     "2025-01-22"),
        ]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in sample_items:
            db.execute(
                "INSERT INTO items (name, category, description, location, date_found, status, submitted) VALUES (?,?,?,?,?,'approved',?)",
                (*item, now)
            )
        db.commit()
    db.close()


def enrich_items(rows):
    """Add emoji and placeholder_url to item rows."""
    result = []
    for row in rows:
        d = dict(row)
        d["emoji"] = CATEGORY_EMOJI.get(d["category"], "📦")
        d["placeholder_url"] = CATEGORY_PHOTOS.get(d["category"])
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
            "INSERT INTO items (name, category, description, location, date_found, photo, submitted) VALUES (?,?,?,?,?,?,?)",
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
