import os, secrets
from datetime import date, datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, init_db

FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
app = Flask(__name__, static_folder=None)
CORS(app)
init_db()
TOKEN_DAYS = 7

def err(msg, code=400):
    return jsonify({"error": msg}), code

def require_auth(admin=False):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            db = get_db()
            row = db.execute("SELECT u.*, t.created FROM tokens t JOIN users u ON u.id=t.user_id WHERE t.token=?", (token,)).fetchone()
            if not row or datetime.fromisoformat(row["created"]) < datetime.now() - timedelta(days=TOKEN_DAYS):
                db.close(); return err("Please sign in", 401)
            if admin and row["role"] != "admin":
                db.close(); return err("Admin access required", 403)
            g.user, g.db = row, db
            try:
                return fn(*a, **kw)
            finally:
                db.close()
        return wrapper
    return deco

def issue_token(db, user):
    token = secrets.token_hex(24)
    db.execute("INSERT INTO tokens(token,user_id,created) VALUES (?,?,?)", (token, user["id"], datetime.now().isoformat()))
    db.commit()
    return jsonify({"token": token, "user": {"username": user["username"], "name": user["name"], "role": user["role"]}})

# ---------- auth ----------
@app.post("/api/login")
def login():
    d = request.get_json(silent=True) or {}
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE username=?", (str(d.get("username", "")).strip().lower(),)).fetchone()
    if not u or not check_password_hash(u["password_hash"], str(d.get("password", ""))):
        db.close(); return err("Incorrect username or password", 401)
    res = issue_token(db, u); db.close(); return res

@app.post("/api/register")
def register():
    d = request.get_json(silent=True) or {}
    un, pw, name = str(d.get("username", "")).strip().lower(), str(d.get("password", "")), str(d.get("name") or "").strip()
    if len(un) < 3: return err("Username must be at least 3 characters")
    if len(pw) < 6: return err("Password must be at least 6 characters")
    if not name: return err("Name is required")
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
        db.close(); return err("That username is taken", 409)
    db.execute("INSERT INTO users(username,name,role,password_hash) VALUES (?,?,?,?)", (un, name, "staff", generate_password_hash(pw)))
    db.commit()
    u = db.execute("SELECT * FROM users WHERE username=?", (un,)).fetchone()
    res = issue_token(db, u); db.close(); return res

@app.get("/api/me")
@require_auth()
def me():
    u = g.user
    return jsonify({"user": {"username": u["username"], "name": u["name"], "role": u["role"]}})

# ---------- data ----------
@app.get("/api/all")
@require_auth()
def all_data():
    q = lambda s: [dict(r) for r in g.db.execute(s)]
    return jsonify({
        "authors": q("SELECT id,name,country,born,bio FROM authors ORDER BY id"),
        "books": q("SELECT b.id,b.title,a.name AS author,b.genre,b.year,b.copies FROM books b JOIN authors a ON a.id=b.author_id ORDER BY b.id"),
        "loans": q("SELECT id,book_id AS bookId,member,issued,due,returned FROM loans ORDER BY id")})

def book_payload(d):
    title, genre = str(d.get("title", "")).strip(), str(d.get("genre", "")).strip()
    row = g.db.execute("SELECT id FROM authors WHERE name=?", (d.get("author"),)).fetchone()
    try: year, copies = int(d.get("year")), int(d.get("copies"))
    except (TypeError, ValueError): return None, "Year and copies must be numbers"
    if not title or len(title) > 120: return None, "Title is required (max 120 chars)"
    if not row: return None, "Unknown author"
    if copies < 1: return None, "Copies must be at least 1"
    return (title, row["id"], genre, year, copies), None

@app.post("/api/books")
@require_auth()
def add_book():
    vals, e = book_payload(request.get_json(silent=True) or {})
    if e: return err(e)
    g.db.execute("INSERT INTO books(title,author_id,genre,year,copies) VALUES (?,?,?,?,?)", vals); g.db.commit()
    return jsonify({"ok": True}), 201

@app.put("/api/books/<int:bid>")
@require_auth()
def edit_book(bid):
    vals, e = book_payload(request.get_json(silent=True) or {})
    if e: return err(e)
    g.db.execute("UPDATE books SET title=?,author_id=?,genre=?,year=?,copies=? WHERE id=?", (*vals, bid)); g.db.commit()
    return jsonify({"ok": True})

@app.delete("/api/books/<int:bid>")
@require_auth(admin=True)
def delete_book(bid):
    g.db.execute("DELETE FROM books WHERE id=?", (bid,)); g.db.commit()
    return jsonify({"ok": True})

@app.post("/api/authors")
@require_auth()
def add_author():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip()
    if not name: return err("Name is required")
    if g.db.execute("SELECT 1 FROM authors WHERE name=?", (name,)).fetchone(): return err("Author already exists", 409)
    g.db.execute("INSERT INTO authors(name,country,born,bio) VALUES (?,?,?,?)", (name, d.get("country", ""), d.get("born"), d.get("bio", "")))
    g.db.commit()
    return jsonify({"ok": True}), 201

@app.delete("/api/authors/<int:aid>")
@require_auth(admin=True)
def delete_author(aid):
    if g.db.execute("SELECT 1 FROM books WHERE author_id=?", (aid,)).fetchone(): return err("Remove this author's books first", 409)
    g.db.execute("DELETE FROM authors WHERE id=?", (aid,)); g.db.commit()
    return jsonify({"ok": True})

@app.post("/api/loans")
@require_auth()
def issue_loan():
    d = request.get_json(silent=True) or {}
    book = g.db.execute("SELECT copies FROM books WHERE id=?", (d.get("bookId"),)).fetchone()
    member = str(d.get("member", "")).strip()
    if not book: return err("Book not found", 404)
    if not member: return err("Member name is required")
    out = g.db.execute("SELECT COUNT(*) c FROM loans WHERE book_id=? AND returned IS NULL", (d["bookId"],)).fetchone()["c"]
    if out >= book["copies"]: return err("No copies available", 409)
    g.db.execute("INSERT INTO loans(book_id,member,issued,due) VALUES (?,?,?,?)", (d["bookId"], member, date.today().isoformat(), d.get("due"))); g.db.commit()
    return jsonify({"ok": True}), 201

@app.post("/api/loans/<int:lid>/return")
@require_auth()
def return_loan(lid):
    g.db.execute("UPDATE loans SET returned=? WHERE id=? AND returned IS NULL", (date.today().isoformat(), lid)); g.db.commit()
    return jsonify({"ok": True})

# ---------- serve the frontend ----------
@app.get("/")
def home():
    return send_from_directory(FRONTEND, "index.html")

@app.get("/<path:name>")
def assets(name):
    return send_from_directory(FRONTEND, name)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
