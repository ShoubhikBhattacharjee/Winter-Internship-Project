from flask import Flask, send_file, request, abort
import json
from pathlib import Path

app = Flask(__name__)

DATA_DIR = Path("../Data")
KB = json.loads((DATA_DIR / "meta.json").read_text())
NOTES_DIR = Path("../Notes")

@app.get("/fetch")
def fetch():
    item_id = request.args.get("id")
    ext = request.args.get("ext")

    item = next((i for i in KB if i["id"] == item_id), None)
    if not item:
        abort(404)

    path = item["source"]["path"].get(ext)
    if not path:
        abort(404)

    file_path = NOTES_DIR / path
    if not file_path.exists():
        abort(404)

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(port=8001)
