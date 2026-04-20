from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import re

app = Flask(__name__)
CORS(app)

DB_PATH = 'qa_portal.db'


# ================== DB INIT ================== #
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # جداول أساسية (لو موجودة مسبقاً ما راح يعيد إنشاءها)
    c.execute('''CREATE TABLE IF NOT EXISTS test_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    steps TEXT,
                    expected TEXT,
                    actual TEXT,
                    status TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bug_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    priority TEXT,
                    steps TEXT,
                    expected TEXT,
                    actual TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )''')

    conn.commit()

    # نحاول نضيف أعمدة المراجعة لو ناقصة (آمنة حتى لو موجودة)
    try:
        c.execute("ALTER TABLE test_cases ADD COLUMN user_email TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE test_cases ADD COLUMN reported_by TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE test_cases ADD COLUMN reported_at TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE test_cases ADD COLUMN review_status TEXT DEFAULT 'Pending'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE test_cases ADD COLUMN comment TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE test_cases ADD COLUMN review_comment TEXT")
    except Exception:
        pass

    try:
        c.execute("ALTER TABLE bug_reports ADD COLUMN user_email TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE bug_reports ADD COLUMN reported_by TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE bug_reports ADD COLUMN reported_at TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE bug_reports ADD COLUMN review_status TEXT DEFAULT 'Pending'")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE bug_reports ADD COLUMN comment TEXT")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE bug_reports ADD COLUMN review_comment TEXT")
    except Exception:
        pass

    conn.commit()
    conn.close()


init_db()


# ================== HELPERS ================== #
ALLOWED_DOMAINS = {"gmail.com", "jodayn.com"}

def allowed_email(email: str) -> bool:
    try:
        domain = email.strip().split("@", 1)[1].lower()
    except Exception:
        return False
    return domain in ALLOWED_DOMAINS

def valid_password(pw: str) -> bool:
    return bool(re.fullmatch(r"\d{8}", pw or ""))


# ================== ROOT ================== #
@app.route('/')
def home():
    return "<h2>✅ QA Training Portal Backend is running successfully!</h2>"


# ================== AUTH ================== #
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()
    role = (data.get('role') or 'user').strip().lower()

    if not name or not email or not password:
        return jsonify({"ok": False, "message": "Please fill all fields."}), 400

    if not allowed_email(email):
        return jsonify({"ok": False, "message": "Email domain not allowed (gmail/jodayn only)."}), 400

    if not valid_password(password):
        return jsonify({"ok": False, "message": "Password must be exactly 8 digits."}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                  (name, email, password, role))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return jsonify({"ok": True, "message": "Account created 🎉", "user": {
            "id": user_id, "name": name, "email": email, "role": role
        }})
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "message": "Email already registered."}), 409


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({"ok": False, "message": "Please enter email & password."}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, email, role FROM users WHERE email=? AND password=?", (email, password))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"ok": False, "message": "Invalid credentials."}), 401

    return jsonify({"ok": True, "message": "Login successful", "user": {
        "id": row[0], "name": row[1], "email": row[2], "role": row[3]
    }})


# ================== TEST CASES ================== #
@app.route('/add_testcase', methods=['POST'])
def add_testcase():
    data = request.get_json(force=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO test_cases (title, steps, expected, actual, status, reported_by, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        f"ID:{data.get('id','')} | Module:{data.get('module','')} | Actor:{data.get('actor','')} | Scenario:{data.get('scenario','')}",
        data.get('steps',''),
        data.get('expected',''),
        data.get('actual',''),
        data.get('status',''),
        data.get('reported_by', ''),   # من الفرونت نحط userName
        'Pending'
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "✅ Test case added successfully!"})


@app.route('/get_testcases', methods=['GET'])
def get_testcases():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, title, steps, expected, actual, status, reported_by, review_status, review_comment
        FROM test_cases
    """)
    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        db_id = r[0]
        title_text = r[1] or ""
        parts = title_text.split("|")
        result.append({
            "db_id": db_id,  # مهم للفرونت
            "id":        parts[0].replace("ID:", "").strip() if len(parts) > 0 else "",
            "module":    parts[1].replace("Module:", "").strip() if len(parts) > 1 else "",
            "actor":     parts[2].replace("Actor:", "").strip() if len(parts) > 2 else "",
            "scenario":  parts[3].replace("Scenario:", "").strip() if len(parts) > 3 else "",
            "steps":     r[2],
            "expected":  r[3],
            "actual":    r[4],
            "status":    r[5],
            "reported_by":    r[6],
            "review_status":  r[7] or "",
            "review_comment": r[8] or ""
        })
    return jsonify(result)


@app.route('/edit_testcase/<int:tc_id>', methods=['PUT'])
def edit_testcase(tc_id):
    data = request.get_json(force=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE test_cases
        SET title=?, steps=?, expected=?, actual=?, status=?
        WHERE id=?
    """, (
        f"ID:{data.get('id','')} | Module:{data.get('module','')} | Actor:{data.get('actor','')} | Scenario:{data.get('scenario','')}",
        data.get('steps',''),
        data.get('expected',''),
        data.get('actual',''),
        data.get('status',''),
        tc_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "✅ Test case updated successfully!"})


@app.route('/delete_testcase/<int:tc_id>', methods=['DELETE'])
def delete_testcase(tc_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM test_cases WHERE id=?", (tc_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "✅ Test case deleted!"})


@app.route('/review_testcase/<int:tc_id>', methods=['PUT'])
def review_testcase(tc_id):
    data = request.get_json(force=True)
    status = data.get("review_status")
    comment = data.get("review_comment", "")

    if status not in ("Approved", "Rejected", "Need to Fix"):
        return jsonify({"ok": False, "message": "Invalid status"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE test_cases
        SET review_status=?, review_comment=?
        WHERE id=?
    """, (status, comment, tc_id))
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "message": "✅ Review saved"})


# ================== BUG REPORTS ================== #
@app.route('/add_bugreport', methods=['POST'])
def add_bugreport():
    data = request.get_json(force=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO bug_reports (title, priority, steps, expected, actual, reported_by, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('title',''),
        data.get('priority',''),
        data.get('steps',''),
        data.get('expected',''),
        data.get('actual',''),
        data.get('reported_by',''),
        'Pending'
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "✅ Bug report added successfully!"})


@app.route('/get_bugreports', methods=['GET'])
def get_bugreports():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, title, priority, steps, expected, actual, reported_by, review_status, review_comment
        FROM bug_reports
    """)
    rows = c.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id":            r[0],
            "title":         r[1],
            "priority":      r[2],
            "steps":         r[3],
            "expected":      r[4],
            "actual":        r[5],
            "reported_by":   r[6],
            "review_status":  r[7] or "",
            "review_comment": r[8] or ""
        })
    return jsonify(result)


@app.route('/edit_bugreport/<int:bug_id>', methods=['PUT'])
def edit_bugreport(bug_id):
    data = request.get_json(force=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE bug_reports
        SET title=?, priority=?, steps=?, expected=?, actual=?
        WHERE id=?
    """, (
        data.get('title',''),
        data.get('priority',''),
        data.get('steps',''),
        data.get('expected',''),
        data.get('actual',''),
        bug_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "✅ Bug report updated!"})


@app.route('/delete_bugreport/<int:id>', methods=['DELETE'])
def delete_bugreport(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM bug_reports WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "✅ Bug report deleted!"})


@app.route('/review_bugreport/<int:bug_id>', methods=['PUT'])
def review_bugreport(bug_id):
    data = request.get_json(force=True)
    status = data.get("review_status")
    comment = data.get("review_comment", "")

    if status not in ("Approved", "Rejected", "Need to Fix"):
        return jsonify({"ok": False, "message": "Invalid status"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE bug_reports
        SET review_status=?, review_comment=?
        WHERE id=?
    """, (status, comment, bug_id))
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "message": "✅ Review saved"})


# ================== RUN ================== #
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True)