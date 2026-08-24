from pathlib import Path
import re

KB_DIR = Path("knowledge_base")
COLLECTION_NAME = "smartassist_kb"

class RAGEngine:
    def __init__(self):
        self.collection = None
        self.available = False
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.client = chromadb.PersistentClient(path="data/chroma")
            self.collection = self.client.get_or_create_collection(COLLECTION_NAME)
            self.available = True
        except Exception as e:
            print("RAG initialization warning:", e)

    def _load_articles(self):
        articles = []
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = path.stem.replace("_", " ").title()
            articles.append((path.name, title, text))
        return articles

    def rebuild(self):
        if not self.available:
            return
        articles = self._load_articles()
        if not articles:
            return
        ids = [a[0] for a in articles]
        docs = [a[2] for a in articles]
        metas = [{"filename": a[0], "title": a[1]} for a in articles]
        embeddings = self.model.encode(docs).tolist()
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(COLLECTION_NAME)
        self.collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    def ensure_index(self):
        if self.available and self.collection.count() == 0:
            self.rebuild()

    def search(self, query, top_k=3):
        self.ensure_index()
        if not self.available or self.collection.count() == 0:
            return []
        emb = self.model.encode([query]).tolist()
        result = self.collection.query(query_embeddings=emb, n_results=top_k)
        items = []
        for i, doc in enumerate(result["documents"][0]):
            distance = result["distances"][0][i] if result.get("distances") else 1.0
            score = max(0.0, 1.0 - float(distance))
            items.append({"document": doc, "score": round(score, 3), "metadata": result["metadatas"][0][i]})
        return items

    def add_article(self, filename, content):
        filename = re.sub(r"[^a-zA-Z0-9_-]", "_", filename).strip("_") or "article"
        if not filename.endswith(".md"):
            filename += ".md"
        (KB_DIR / filename).write_text(content, encoding="utf-8")
        self.rebuild()
        return filename
