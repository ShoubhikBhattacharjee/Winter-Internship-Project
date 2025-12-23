from sentence_transformers import SentenceTransformer
import faiss, json, numpy as np, os
from pathlib import Path

DATA_DIR = Path("./Data")
KB_PATH = DATA_DIR / "kb.json"   # This is a relative path. It needs to be changed based on the directory in which you run this code.
print(f"Directory = {KB_PATH}")         # Directory Check. Always ensure the directory in which you run the code results in the path being translated to the correct directory.
INDEX_PATH = DATA_DIR / "embeddings.faiss"
META_PATH = DATA_DIR / "meta.json"

model = SentenceTransformer("all-MiniLM-L6-v2")

def main():
    DATA_DIR.mkdir(exist_ok=True)
    kb = json.loads(KB_PATH.read_text("utf8"))

    # Text for embeddings
    texts = [item["question"] + " " + item["answer"] for item in kb]

    emb = model.encode(texts, convert_to_numpy=True)
    faiss.normalize_L2(emb)

    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(kb, indent=2))

    print("Index built and saved.")

if __name__ == "__main__":
    main()
