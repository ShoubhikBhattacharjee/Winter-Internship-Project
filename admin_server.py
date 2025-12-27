import json
import uuid
import subprocess
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    abort,
    send_file
)
from werkzeug.utils import secure_filename

# ===============================
# PATH CONFIG
# ===============================

BASE_DIR = Path(__file__).parent
ADMIN_DIR = BASE_DIR / "admin"
TEMPLATE_DIR = ADMIN_DIR / "templates"
STATIC_DIR = ADMIN_DIR / "static"

KB_PATH = BASE_DIR / "Data" / "kb.json"
TRAIN_SCRIPT = BASE_DIR / "training" / "train_index.py"
UPLOAD_DIR = BASE_DIR / "Notes" / "Uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ===============================
# FLASK APP
# ===============================

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR)
)

# ===============================
# TOKEN STORAGE
# ===============================

active_admin_tokens = set()

# ===============================
# TOKEN GENERATION
# ===============================

@app.route("/generate-token")
def generate_token():
    token = uuid.uuid4().hex
    active_admin_tokens.add(token)
    return jsonify({"admin_url": f"http://localhost:5000/admin/{token}"})

# ===============================
# ADMIN PAGE
# ===============================

@app.route("/admin/<token>")
def admin_page(token):
    if token not in active_admin_tokens:
        abort(404)
    active_admin_tokens.remove(token)
    return render_template("admin.html")

# ===============================
# HELPER: GENERATE READABLE ID
# ===============================

def generate_readable_id(kb):
    today = datetime.now().strftime("%Y-%m-%d")
    count = sum(1 for e in kb if e.get("id", "").startswith(today))
    return f"{today}-{str(count + 1).zfill(3)}"

# ===============================
# HELPER: SAFE FILE SAVE
# ===============================

def save_file_preserve_name(uploaded_file):
    original_name = secure_filename(uploaded_file.filename)
    target = UPLOAD_DIR / original_name

    if not target.exists():
        uploaded_file.save(target)
        return target

    # Handle duplicates: file(1).pdf
    stem = target.stem
    suffix = target.suffix
    i = 1
    while True:
        new_target = UPLOAD_DIR / f"{stem}({i}){suffix}"
        if not new_target.exists():
            uploaded_file.save(new_target)
            return new_target
        i += 1

# ===============================
# REBUILD INDEX
# ===============================

def rebuild_index():
    subprocess.run(["python", str(TRAIN_SCRIPT)], check=False)

# ===============================
# READ + SEARCH
# ===============================

@app.route("/api/data")
def api_data():
    q = request.args.get("q", "").lower()

    if KB_PATH.exists() and KB_PATH.stat().st_size > 0:
        kb = json.loads(KB_PATH.read_text("utf-8"))
    else:
        kb = []

    if q:
        kb = [
            e for e in kb
            if q in e.get("id", "").lower()
            or q in e.get("question", "").lower()
            or q in ",".join(e.get("tags", [])).lower()
        ]

    return jsonify(kb)

# ===============================
# ADD / UPDATE ENTRY
# ===============================

@app.route("/api/save", methods=["POST"])
def save_entry():
    # Load existing KB or initialize empty
    if KB_PATH.exists() and KB_PATH.stat().st_size > 0:
        kb = json.loads(KB_PATH.read_text("utf-8"))
    else:
        kb = []

    entry_id = request.form.get("id")
    if not entry_id:
        entry_id = generate_readable_id(kb)

    uploaded_file = request.files.get("file")
    source = None
    if uploaded_file:
        saved_path = save_file_preserve_name(uploaded_file)
        source = {
            "type": "file",
            "path": {
                saved_path.suffix: str(saved_path.relative_to(BASE_DIR))
            }
        }

    entry = {
        "id": entry_id,
        "question": request.form["question"],
        "answer": request.form["answer"],
        "tags": (
            request.form["tags"].split(",")
            if request.form.get("tags") else []
        ),
        "notes": request.form.get("notes"),
        "created_at": datetime.now().isoformat(),
        "source": source
    }

    # Update existing entry if found, else append
    updated = False
    for i, e in enumerate(kb):
        if e["id"] == entry_id:
            kb[i] = entry
            updated = True
            break
    if not updated:
        kb.append(entry)

    KB_PATH.write_text(json.dumps(kb, indent=2, ensure_ascii=False))
    rebuild_index()
    return "", 200

# ===============================
# DELETE ENTRY
# ===============================

@app.route("/api/delete/<entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    if KB_PATH.exists() and KB_PATH.stat().st_size > 0:
        kb = json.loads(KB_PATH.read_text("utf-8"))
    else:
        kb = []

    kb = [e for e in kb if e["id"] != entry_id]
    KB_PATH.write_text(json.dumps(kb, indent=2, ensure_ascii=False))
    rebuild_index()
    return "", 200

# ===============================
# SERVE FILE BY ENTRY ID
# ===============================

@app.route("/files/by-id/<entry_id>")
def serve_file_by_entry_id(entry_id):
    if KB_PATH.exists() and KB_PATH.stat().st_size > 0:
        kb = json.loads(KB_PATH.read_text("utf-8"))
    else:
        kb = []

    entry = next((e for e in kb if e.get("id") == entry_id), None)
    if not entry or not entry.get("source"):
        abort(404)

    ext = next(iter(entry["source"]["path"]))
    rel_path = entry["source"]["path"][ext]
    file_path = (BASE_DIR / rel_path).resolve()

    if not file_path.exists():
        abort(404)

    return send_file(file_path)

# ===============================
if __name__ == "__main__":
    app.run(debug=True)
