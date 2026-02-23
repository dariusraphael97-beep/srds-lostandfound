# SRDS Lost & Found Website
## Saddle River Day School — FBLA Website Coding & Development 2025-2026

---

## 🚀 Setup & Running Instructions

### Prerequisites
- Python 3.8 or higher installed
- pip (Python package manager)

### Step 1 — Install Dependencies
Open your terminal in the project folder and run:
```
pip install -r requirements.txt
```

### Step 2 — Run the Website
```
python app.py
```

### Step 3 — Open in Browser
Visit: **http://127.0.0.1:5000**

---

## 🔐 Admin Access
- URL: http://127.0.0.1:5000/admin
- Password: `srds2026`

---

## 📁 Project Structure
```
srds-lostandfound/
├── app.py                  ← Main Flask backend (Python)
├── requirements.txt        ← Python dependencies
├── lostandfound.db         ← SQLite database (auto-created on first run)
├── static/
│   ├── css/
│   │   └── style.css       ← All styles
│   └── uploads/            ← Uploaded item photos (auto-created)
└── templates/
    ├── base.html           ← Base layout (nav, footer, flash messages)
    ├── index.html          ← Homepage
    ├── items.html          ← Browse all items (with search & filter)
    ├── report.html         ← Report a found item form
    ├── claim.html          ← Claim an item form
    ├── admin_login.html    ← Admin login page
    └── admin.html          ← Admin dashboard
```

---

## 🛠 Technologies Used
- **Backend:** Python 3, Flask (micro web framework), SQLite (database)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Fonts:** Playfair Display, DM Sans (Google Fonts)
- **File Uploads:** werkzeug secure_filename

---

## ✨ Key Features
1. **Homepage** — Statistics, recent items, how-it-works guide
2. **Item Browser** — Search by keyword, filter by category
3. **Report Form** — Submit found items with photo upload
4. **Claim Form** — Request to claim a listed item with student ID verification
5. **Admin Dashboard** — Approve/reject items, manage claims, view history
6. **Responsive Design** — Works on desktop, tablet, and mobile
7. **Accessibility** — ARIA labels, keyboard navigation, color contrast, alt text

---

## 📚 Sources & References
- Flask Documentation: https://flask.palletsprojects.com/
- SQLite Documentation: https://www.sqlite.org/docs.html
- WCAG Accessibility Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Google Fonts: https://fonts.google.com/
- Werkzeug Documentation: https://werkzeug.palletsprojects.com/
