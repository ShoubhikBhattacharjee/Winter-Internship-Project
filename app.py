import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / Path("Data")

KB_PATH = DATA_DIR / Path("kb.json")
ADMIN_PATH = BASE_DIR / Path("admin_identity.json")

app = Flask(
    __name__,
    template_folder="admin/templates",
    static_folder="admin/static"
)

# ------------------------
# Pages
# ------------------------

@app.route("/")
def dashboard():
    admin = json.loads(ADMIN_PATH.read_text())
    return render_template("dashboard.html", admin=admin)

@app.route("/create")
def create_entry_page():
    admin = json.loads(ADMIN_PATH.read_text())
    return render_template(
        "entry_form.html",
        admin=admin,
        mode="Create",
        submit_url="/api/save",
        method="POST",
        entry=None
    )

@app.route("/edit/<entry_id>")
def edit_entry_page(entry_id):
    admin = json.loads(ADMIN_PATH.read_text())
    kb = json.loads(KB_PATH.read_text())

    entry = next(e for e in kb if e["id"] == entry_id)

    return render_template(
        "entry_form.html",
        admin=admin,
        mode="Update",
        submit_url=f"/api/save/{entry_id}",
        method="POST",
        entry=entry
    )

# ------------------------
# APIs
# ------------------------

@app.route("/api/data")
def api_data():
    return jsonify(json.loads(KB_PATH.read_text()))

@app.route("/api/save", methods=["POST"])
@app.route("/api/save/<entry_id>", methods=["POST"])
def save_entry(entry_id=None):
    kb = json.loads(KB_PATH.read_text())

    if entry_id:
        entry = next(e for e in kb if e["id"] == entry_id)
        entry.update({
            "question": request.form["question"],
            "answer": request.form["answer"],
            "tags": request.form["tags"].split(","),
            "notes": request.form.get("notes"),
            "modified": request.form.get("modified")
        })
    else:
        kb.append({
            "id": f"TEST-{len(kb)+1}",
            "question": request.form["question"],
            "answer": request.form["answer"],
            "tags": request.form["tags"].split(","),
            "created_at": "2025-01-07T00:00:00+05:30"
        })

    KB_PATH.write_text(json.dumps(kb, indent=2))
    return "", 200

@app.route("/api/delete/<entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    kb = json.loads(KB_PATH.read_text())
    kb = [e for e in kb if e["id"] != entry_id]
    KB_PATH.write_text(json.dumps(kb, indent=2))
    return "", 200

# ------------------------

if __name__ == "__main__":
    app.run(debug=True)
