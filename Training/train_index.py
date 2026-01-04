from sentence_transformers import SentenceTransformer
import faiss
import json
from pathlib import Path

# ---------------- CONFIG ----------------
DATA_DIR = Path("./Data")
INDEX_PATH = DATA_DIR / "embeddings.faiss"
META_PATH = DATA_DIR / "meta.json"

MODEL_NAME = "all-MiniLM-L6-v2"
# ----------------------------------------

model = SentenceTransformer(MODEL_NAME)


def load_all_json_files(base_dir: Path):
    """
    Recursively load and merge all JSON files under base_dir,
    excluding generated files.
    """
    all_items = []

    for file in sorted(base_dir.rglob("*.json")):
        # Skip generated/meta files
        if file.name in {"meta.json", "kb.json"}:
            continue

        # Skip hidden or temp files if any
        if file.name.startswith("."):
            continue

        print(f"Loading: {file.relative_to(base_dir)}")

        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise RuntimeError(f"❌ Invalid JSON in {file}") from e

        if not isinstance(data, list):
            raise ValueError(f"❌ {file} does not contain a JSON list")

        for idx, item in enumerate(data):
            if "question" not in item or "answer" not in item:
                raise ValueError(
                    f"❌ Invalid entry in {file} at index {idx} "
                    "(missing question/answer)"
                )

            # Optional: embed file trace for debugging (non-breaking)
            item["_source_file"] = str(file.relative_to(base_dir))

            all_items.append(item)

    if not all_items:
        raise RuntimeError("❌ No valid knowledge JSON files found!")

    return all_items


def build_faiss_index(texts):
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True
    )

    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return index


def main():
    DATA_DIR.mkdir(exist_ok=True)

    print("🔍 Scanning knowledge base directories...")
    kb = load_all_json_files(DATA_DIR)

    print(f"📚 Total knowledge entries loaded: {len(kb)}")

    texts = [
        f"{item['question']} {item['answer']}"
        for item in kb
    ]

    print("🧠 Generating embeddings & building FAISS index...")
    index = build_faiss_index(texts)

    print("💾 Saving index and metadata...")
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(kb, indent=2), encoding="utf-8")

    print("✅ Training complete!")
    print(f"📌 Index saved to: {INDEX_PATH}")
    print(f"📌 Metadata saved to: {META_PATH}")


if __name__ == "__main__":
    main()
