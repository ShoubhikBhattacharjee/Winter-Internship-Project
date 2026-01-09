import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from admin_access import touch_activity

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / Path("Data")

ADMIN_PATH = BASE_DIR / Path("admin_identity.json")

app = Flask(
    __name__,
    template_folder="admin/templates",
    static_folder="admin/static"
)

ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV",
    5: "V", 6: "VI", 7: "VII", 8: "VIII"
}

SUBJECTS_PATH = BASE_DIR / "subjects.json"

def load_subjects():
    if not SUBJECTS_PATH.exists():
        SUBJECTS_PATH.write_text("{}")
    return json.loads(SUBJECTS_PATH.read_text())

def save_subjects(subjects):
    SUBJECTS_PATH.write_text(json.dumps(subjects, indent=2))


def sem_to_roman(sem: int) -> str:
    if sem not in ROMAN:
        raise ValueError("Unsupported semester")
    return ROMAN[sem]

def resolve_json_file(semester, subject, module):
    roman = sem_to_roman(semester)

    sem_dir = DATA_DIR / f"Sem-{roman}"
    subject_dir = sem_dir / subject
    subject_dir.mkdir(parents=True, exist_ok=True)

    file_path = subject_dir / f"Sem-{roman}_{subject}_Mod-{module}.json"

    if not file_path.exists():
        file_path.write_text("[]")

    return file_path


def resolve_subject(subject_input: str) -> str:
    subjects = load_subjects()

    normalized = subject_input.strip().lower()

    # Match by acronym
    for code in subjects:
        if code.lower() == normalized:
            return code

    # Match by full name
    for code, name in subjects.items():
        if name.lower() == normalized:
            return code

    # New subject → register
    new_code = subject_input.strip().upper().replace(" ", "_")
    subjects[new_code] = subject_input.strip()
    save_subjects(subjects)

    return new_code


def next_serial(entries):
    if not entries:
        return 1

    serials = []
    for e in entries:
        try:
            serials.append(int(e["id"].split("_")[-1]))
        except Exception:
            pass

    return max(serials, default=0) + 1


def generate_id(semester, subject, module, serial):
    return f"S{semester}_{subject}_M{module}_{serial:03d}"


def parse_id(entry_id):
    # S3_AME_I_M1_001
    parts = entry_id.split("_")
    semester = int(parts[0][1:])
    subject = parts[1]
    module = int(parts[2][1:])
    return semester, subject, module

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
    subjects = load_subjects()

    return render_template(
        "entry_form.html",
        admin=admin,
        subjects=subjects,
        mode="Create",
        submit_url="/api/save",
        method="POST",
        entry=None
    )


# ------------------------
# APIs
# ------------------------

@app.before_request
def track_admin_activity():
    if request.path.startswith("/api") or request.path.startswith("/admin"):
        touch_activity()


@app.route("/api/data")
def api_data():
    all_entries = []

    for json_file in DATA_DIR.rglob("*.json"):
        try:
            all_entries.extend(json.loads(json_file.read_text()))
        except Exception:
            pass

    return jsonify(all_entries)


@app.route("/api/save", methods=["POST"])
def create_entry():
    semester = int(request.form["semester"])
    # subject = request.form["subject"]
    subject_input = request.form["subject"]
    subject = resolve_subject(subject_input)
    module = int(request.form["module"])

    file_path = resolve_json_file(semester, subject, module)
    entries = json.loads(file_path.read_text())

    serial = next_serial(entries)
    entry_id = generate_id(semester, subject, module, serial)

    entry = {
        "id": entry_id,
        "question": request.form["question"],
        "answer": request.form["answer"],
        "tags": [t.strip() for t in request.form["tags"].split(",") if t.strip()],
        "source": {
            "type": request.form.get("source_type", "file"),
            "path": request.form.get("source_path"),
            "url": request.form.get("source_url")
        },
        "created_at": datetime.now().isoformat(),
        "notes": request.form.get("notes")
    }

    entries.append(entry)
    file_path.write_text(json.dumps(entries, indent=2))

    return jsonify(entry), 201

@app.route("/edit/<entry_id>")
def edit_entry_page(entry_id):
    admin = json.loads(ADMIN_PATH.read_text())
    subjects = load_subjects()

    semester, subject, module = parse_id(entry_id)
    file_path = resolve_json_file(semester, subject, module)

    entries = json.loads(file_path.read_text())
    entry = next(e for e in entries if e["id"] == entry_id)

    # inject routing metadata for form
    entry["_semester"] = semester
    entry["_subject"] = subject
    entry["_module"] = module

    return render_template(
        "entry_form.html",
        admin=admin,
        subjects=subjects,
        mode="Update",
        submit_url=f"/api/save/{entry_id}",
        method="POST",
        entry=entry
    )


@app.route("/api/save/<entry_id>", methods=["POST"])
def update_entry(entry_id):
    semester, subject, module = parse_id(entry_id)
    file_path = resolve_json_file(semester, subject, module)

    entries = json.loads(file_path.read_text())
    entry = next(e for e in entries if e["id"] == entry_id)

    entry.update({
        "question": request.form["question"],
        "answer": request.form["answer"],
        "tags": [t.strip() for t in request.form["tags"].split(",") if t.strip()],
        "notes": request.form.get("notes"),
        "modified": datetime.now().isoformat()
    })

    file_path.write_text(json.dumps(entries, indent=2))
    return jsonify(entry), 200

@app.route("/api/delete/<entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    semester, subject, module = parse_id(entry_id)
    file_path = resolve_json_file(semester, subject, module)

    entries = json.loads(file_path.read_text())
    entries = [e for e in entries if e["id"] != entry_id]

    file_path.write_text(json.dumps(entries, indent=2))
    return "", 204

# ------------------------

if __name__ == "__main__":
    app.run(debug=True)
