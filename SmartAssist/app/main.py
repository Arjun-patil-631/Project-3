from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uuid

from .database import (
    init_db,
    add_message,
    get_history,
    add_feedback,
    all_conversations,
    all_feedback,
)
from .preprocess import classify_intent, detect_frustration, is_prompt_injection
from .rag import RAGEngine
from .llm import generate_response

app = FastAPI(title="SmartAssist", version="1.1")

app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()
rag = RAGEngine()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    rating: str
    comment: str = ""


class ArticleRequest(BaseModel):
    filename: str
    content: str


@app.get("/", response_class=HTMLResponse)
def home():
    return Path("static/index.html").read_text(encoding="utf-8")


@app.get("/admin", response_class=HTMLResponse)
def admin():
    return Path("static/admin.html").read_text(encoding="utf-8")


@app.post("/chat")
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    message = req.message.strip()

    if not message:
        return {
            "session_id": session_id,
            "response": "Please enter a message.",
            "intent": "faq",
            "escalate": False,
            "sources": [],
        }

    intent = classify_intent(message)

    if is_prompt_injection(message):
        response = (
            "I can help with customer-support questions, but I can’t reveal "
            "hidden instructions or bypass safety rules."
        )

        add_message(session_id, "user", message, intent)
        add_message(session_id, "assistant", response, intent)

        return {
            "session_id": session_id,
            "response": response,
            "intent": intent,
            "escalate": False,
            "sources": [],
        }

    history = get_history(session_id)
    results = rag.search(message, top_k=3)

    context = "\n\n".join(r["document"] for r in results)
    best_score = results[0]["score"] if results else 0.0

    escalate = (
        intent == "escalation"
        or detect_frustration(message)
        or best_score < 0.28
    )

    response = generate_response(message, context, history)

    if escalate and "human" not in response.lower():
        response += (
            "\n\nIf this issue needs personal assistance, "
            "I recommend a human support agent."
        )

    add_message(session_id, "user", message, intent)
    add_message(session_id, "assistant", response, intent)

    return {
        "session_id": session_id,
        "response": response,
        "intent": intent,
        "escalate": escalate,
        "sources": [
            {
                "title": r["metadata"].get("title", "Knowledge article"),
                "score": r["score"],
            }
            for r in results
        ],
    }


@app.get("/history/{session_id}")
def history(session_id: str):
    return {
        "session_id": session_id,
        "messages": get_history(session_id, 50),
    }


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    rating = req.rating.strip().lower()

    if rating not in {"helpful", "not helpful"}:
        raise HTTPException(
            status_code=400,
            detail="Rating must be 'helpful' or 'not helpful'.",
        )

    add_feedback(req.session_id, rating, req.comment.strip())

    return {
        "ok": True,
        "session_id": req.session_id,
        "rating": rating,
    }


# ---------------- ADMIN: KNOWLEDGE BASE ----------------

@app.get("/admin/knowledge")
def knowledge():
    articles = []

    for p in sorted(Path("knowledge_base").glob("*.md")):
        articles.append(
            {
                "filename": p.name,
                "content": p.read_text(encoding="utf-8"),
            }
        )

    return {
        "ok": True,
        "count": len(articles),
        "articles": articles,
    }


@app.post("/admin/knowledge")
def add_knowledge(req: ArticleRequest):
    if not req.filename.strip():
        raise HTTPException(status_code=400, detail="Filename is required.")

    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Article content is required.")

    filename = rag.add_article(req.filename, req.content)

    return {
        "ok": True,
        "action": "created_or_updated",
        "filename": filename,
    }


@app.put("/admin/knowledge/{filename}")
def update_knowledge(filename: str, req: ArticleRequest):
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Article content is required.")

    target = Path("knowledge_base") / filename

    if not target.exists():
        raise HTTPException(status_code=404, detail="Article not found.")

    target.write_text(req.content, encoding="utf-8")
    rag.rebuild()

    return {
        "ok": True,
        "action": "updated",
        "filename": filename,
    }


@app.delete("/admin/knowledge/{filename}")
def delete_knowledge(filename: str):
    target = Path("knowledge_base") / filename

    if not target.exists():
        raise HTTPException(status_code=404, detail="Article not found.")

    target.unlink()
    rag.rebuild()

    return {
        "ok": True,
        "action": "deleted",
        "filename": filename,
    }


@app.post("/admin/knowledge/rebuild")
def rebuild_knowledge():
    rag.rebuild()

    return {
        "ok": True,
        "message": "Knowledge-base index rebuilt successfully.",
    }


# ---------------- ADMIN: CONVERSATIONS ----------------

@app.get("/admin/conversations")
def conversations():
    rows = all_conversations()

    return {
        "ok": True,
        "count": len(rows),
        "rows": rows,
    }


# ---------------- ADMIN: FEEDBACK / ANALYTICS ----------------

@app.get("/admin/feedback")
def feedback_logs():
    rows = all_feedback()

    return {
        "ok": True,
        "count": len(rows),
        "rows": rows,
    }


@app.get("/admin/stats")
def stats():
    conversations = all_conversations()
    feedback = all_feedback()

    helpful = sum(1 for row in feedback if row[2] == "helpful")
    not_helpful = sum(1 for row in feedback if row[2] == "not helpful")

    return {
        "ok": True,
        "conversations": len(conversations),
        "feedback_total": len(feedback),
        "helpful": helpful,
        "not_helpful": not_helpful,
    }