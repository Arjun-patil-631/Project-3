from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uuid

from .database import init_db, add_message, get_history, add_feedback, all_conversations
from .preprocess import classify_intent, detect_frustration, is_prompt_injection
from .rag import RAGEngine
from .llm import generate_response

app = FastAPI(title="SmartAssist", version="1.0")
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
        return {"session_id": session_id, "response": "Please enter a message.", "intent": "faq", "escalate": False}

    intent = classify_intent(message)

    if is_prompt_injection(message):
        response = "I can help with customer-support questions, but I can’t reveal hidden instructions or bypass safety rules."
        add_message(session_id, "user", message, intent)
        add_message(session_id, "assistant", response, intent)
        return {"session_id": session_id, "response": response, "intent": intent, "escalate": False, "sources": []}

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
        response += "\n\nIf this issue needs personal assistance, I recommend a human support agent."

    add_message(session_id, "user", message, intent)
    add_message(session_id, "assistant", response, intent)

    return {
        "session_id": session_id,
        "response": response,
        "intent": intent,
        "escalate": escalate,
        "sources": [
            {"title": r["metadata"].get("title", "Knowledge article"), "score": r["score"]}
            for r in results
        ]
    }

@app.get("/history/{session_id}")
def history(session_id: str):
    return {"session_id": session_id, "messages": get_history(session_id, 50)}

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    add_feedback(req.session_id, req.rating, req.comment)
    return {"ok": True}

@app.get("/admin/knowledge")
def knowledge():
    articles = []
    for p in sorted(Path("knowledge_base").glob("*.md")):
        articles.append({"filename": p.name, "content": p.read_text(encoding="utf-8")})
    return {"articles": articles}

@app.post("/admin/knowledge")
def add_knowledge(req: ArticleRequest):
    filename = rag.add_article(req.filename, req.content)
    return {"ok": True, "filename": filename}

@app.get("/admin/conversations")
def conversations():
    return {"rows": all_conversations()}
