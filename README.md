# 🤖 SmartAssist — AI Customer Support Chatbot

SmartAssist is an AI-powered customer support chatbot designed to provide fast, contextual, and reliable assistance for common customer queries.

It combines **Retrieval-Augmented Generation (RAG)** with **Google Gemini**, allowing responses to be grounded in a curated customer-support knowledge base while maintaining conversation context.

---

## ✨ Features

- 🤖 AI-powered customer support using Google Gemini
- 🔎 Retrieval-Augmented Generation (RAG)
- 🧠 Semantic search using Sentence Transformers
- 📚 ChromaDB vector database
- 🎯 Intent classification
- 💬 Conversation memory using SQLite
- 🧑‍💼 Human support escalation
- 🛡️ Prompt-injection protection
- 👍👎 User feedback collection
- 📝 30+ customer-support knowledge-base articles
- 🛠️ Knowledge-base management interface
- 🌐 FastAPI backend with web-based chat interface

---

## 🏗️ Architecture

```text
                 ┌──────────────────┐
                 │      User        │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   FastAPI API    │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Intent Detection │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   RAG Retrieval  │
                 │    ChromaDB      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │  Gemini LLM      │
                 │ Response Engine  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Support Response │
                 └──────────────────┘
