# Customer Service Agent

Self-hosted RAG customer support agent: Django REST backend + Angular frontend +
Postgres/pgvector + Ollama for local embeddings/chat, wired together with Docker Compose.

## Run it

```bash
cp .env.example .env
docker compose up --build
```

First boot pulls the `nomic-embed-text` and `llama3.1` Ollama models, which can take a
while depending on your connection.

| Service   | URL                          |
|-----------|-------------------------------|
| Frontend  | http://localhost:25004        |
| Backend   | http://localhost:25003/api/   |
| Postgres  | localhost:25001                |
| pgAdmin   | http://localhost:25002        |

## Create an admin user

Admin login is required to manage knowledge bases and upload documents.

```bash
docker compose exec backend python manage.py createsuperuser
```

Log in from the frontend's "Admin login" link, then visit `/documents` to create a
knowledge base and upload PDFs.

## How it works

1. Upload a PDF to a knowledge base — it's chunked (1000-word windows, 150-word
   overlap) and embedded via Ollama's `nomic-embed-text`, synchronously, during the
   upload request.
2. Asking a question in the chat embeds the question and does a pgvector
   cosine-distance search across all knowledge bases. If nothing is close enough
   (distance > `RAG_MAX_DISTANCE`, default 0.5), the agent says it doesn't know
   instead of guessing.
3. Otherwise the matched chunks are put in context and passed to Ollama's `llama3.1`
   along with recent conversation history to produce an answer.

## Backend tests

```bash
docker compose exec backend python manage.py test
```
