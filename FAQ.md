# FAQ

## Walk me through this code

This is a self-hosted RAG (Retrieval-Augmented Generation) support bot: Django REST backend, Angular frontend, Postgres+pgvector for vector storage, Ollama for local embeddings and chat — all run via Docker Compose. Two flows: **ingesting documents** into a knowledge base, and **answering questions** against them.

### Data model — `backend/kb/models.py`

Four tables, straightforward hierarchy:
- **KnowledgeBase** — a named collection (auto-slugified).
- **Document** — a PDF uploaded into a KB, with a status machine (`pending → processing → ready`/`failed`).
- **DocumentChunk** — a slice of a document's text plus its 768-dim `VectorField` embedding (768 = `nomic-embed-text`'s output size).
- **Conversation** / **Message** — chat history; each assistant message stores its `sources` (which chunks it drew from) as JSON.

### Ingestion — `backend/kb/services/chunking.py` + `backend/kb/services/ingestion.py`

Triggered synchronously from `DocumentViewSet.perform_create` in `views.py` — the upload HTTP request blocks until embedding finishes, no background queue.

1. `extract_text` pulls per-page text out of the PDF with `pypdf`.
2. Pages get joined and passed to `chunk_text`: a sliding window over words (default 1000 words, 150 overlap — from `settings.CHUNK_SIZE_WORDS`/`CHUNK_OVERLAP_WORDS`). `step = chunk_size - overlap`, and it walks forward until the window reaches the end.
3. Each chunk is embedded individually via `ollama_client.embed` (one HTTP call per chunk — no batching).
4. All chunks are written atomically: existing chunks for that document are deleted, then the new ones are bulk-created, and the document flips to `ready` with a `page_count`. Any exception along the way sets status to `failed` and stores the error, then re-raises.

### Retrieval + answering — `backend/kb/services/retrieval.py`

`answer_question` is the core RAG loop, called from `ChatView` in `views.py`:

1. `retrieve()` embeds the question, then runs a pgvector `CosineDistance` search across **all** `DocumentChunk`s (not scoped to one KB), ordered by distance, top `RAG_TOP_K`.
2. Guardrail: if the closest match's distance exceeds `RAG_MAX_DISTANCE` (default 0.5), it returns nothing — this is what makes the bot say "I don't have information about that" rather than hallucinate from irrelevant chunks.
3. If there are matches, `_build_context_block` formats them as labeled `[KB / Document]` blocks separated by `---`.
4. A system prompt instructs the model to answer only from context and cite the KB. Recent conversation history (`RAG_HISTORY_TURNS`, newest-first then reversed) is appended, then the user's question.
5. `ollama_client.chat` sends it to Ollama's `/api/chat` (llama3.1, non-streaming) and returns the answer text.
6. Back in `ChatView`, both the user question and assistant answer are persisted as `Message` rows, with `sources` attached to the assistant's message for citation display.

### Ollama client — `backend/kb/services/ollama_client.py`

Thin wrapper: `embed()` hits `/api/embeddings`, `chat()` hits `/api/chat`. Both raise a custom `OllamaError` if the response is missing the expected field — no retries, no streaming.

### API surface — `backend/kb/urls.py` + `backend/kb/views.py`

- `POST /auth/login/` — token auth (DRF `Token`), open to anyone.
- `/knowledge-bases/`, `/documents/` — standard DRF viewsets, gated by `IsAdminOrReadOnly`.
- `POST /chat/` — open to anyone (`AllowAny`); creates a conversation if none given, runs `answer_question`, saves both messages.
- `GET /conversations/<id>/` — fetch full history with nested messages.

### Frontend

Angular app with `core/` (auth service, HTTP interceptor for the token, admin route guard) and `pages/` for chat, document management, and admin login.

One thing worth flagging: retrieval searches across *all* knowledge bases together rather than letting a user scope to one — that's a deliberate design choice per the README, not a bug.

---

## What is Django

Django is a Python web framework for building server-side applications — it handles URL routing, database models/ORM, request/response handling, authentication, and an admin interface out of the box.

In this project specifically:
- **Django REST Framework** (DRF), a Django add-on, is used to build the JSON API — that's what `viewsets`, `serializers`, and `APIView` in `views.py` come from.
- Django's ORM defines the data model in `models.py` (`KnowledgeBase`, `Document`, etc.) and maps those Python classes to Postgres tables, including migrations like `0001_initial.py`.
- `config/settings.py`, `config/urls.py`, and `config/wsgi.py` are Django's standard project-level config: settings, root URL routing, and the WSGI entrypoint the server runs.
- The empty `__init__.py` just marks `config/` as a Python package — Django scaffolds one in every app/project directory.

---

## Explain request→view flow, and admin/migrations (both)

### Request → view flow

Django resolves URLs through a chain of `urlpatterns`, matching path prefixes and delegating the rest.

Example: `POST /api/chat/`

**`config/urls.py`** — the project's root router (`ROOT_URLCONF = "config.urls"` in settings):
```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("kb.urls")),   # strips "api/", hands the rest to kb.urls
]
```
`/api/chat/` matches the `"api/"` prefix, so Django strips it and passes `chat/` into `kb.urls`.

**`kb/urls.py`** — the app-level router:
```python
path("chat/", ChatView.as_view(), name="chat"),
```
`chat/` matches exactly, so Django instantiates `ChatView` and calls it. `ChatView` is a DRF `APIView`; `as_view()` wraps it into a function Django's URL resolver can call, which dispatches by HTTP method — `POST` → `ChatView.post(self, request)`.

Before it even reaches the view, the request passes through the `MIDDLEWARE` stack in settings (top to bottom): security headers, CORS, session handling, CSRF, auth, etc. Auth middleware + DRF's `DEFAULT_AUTHENTICATION_CLASSES` (`TokenAuthentication`/`SessionAuthentication`) populate `request.user` — that's what `IsAdminOrReadOnly` checks on the other endpoints.

The `router.register(...)` calls for `KnowledgeBaseViewSet`/`DocumentViewSet` in `kb/urls.py` are a shortcut: DRF's `DefaultRouter` auto-generates the list/detail/create/update/delete URL patterns for a `ModelViewSet`, so you don't hand-write `path()` entries for each CRUD action.

### Admin site & migrations

**Admin** — `django.contrib.admin` (in `INSTALLED_APPS`) is a built-in CRUD UI generated from your models. `path("admin/", admin.site.urls)` mounts it. `kb/admin.py` registers each model with an `@admin.register(...)` decorator and an `admin.ModelAdmin` subclass controlling how it's displayed — e.g. `DocumentAdmin` shows a `list_display` of columns and a `list_filter` sidebar by status/KB. Nothing here is used by the actual chat product; it's purely an internal tool for staff to browse/edit KBs, documents, and conversations directly, reachable at `/admin/` once you `createsuperuser`.

**Migrations** — Django's schema-versioning mechanism. You don't hand-write SQL; you define Python model classes (`models.py`), then run `manage.py makemigrations`, which diffs your models against the last-known schema and generates a migration file like `0001_initial.py`. Each migration is a list of `operations` — here, `CreateModel` for each table plus `AddIndex` for the composite index on `DocumentChunk`. Notably it also includes `pgvector.django.VectorExtension()`, which runs `CREATE EXTENSION vector` on Postgres — migrations aren't just table DDL, they can run arbitrary schema setup. `manage.py migrate` then applies pending migrations in dependency order and records what's been applied in a `django_migrations` table, so it's idempotent across environments (local DB, CI, prod all converge on the same schema by replaying the same ordered steps).

---

## What is a CRUD UI

CRUD UI = an interface for **C**reate, **R**ead, **U**pdate, **D**elete operations on data — the four basic things you do to database records. "CRUD UI" just means a UI that exposes those four operations, typically as list views, detail/edit forms, and delete buttons/confirmations.

In this project, Django's admin (`/admin/`) is a CRUD UI that's *auto-generated* from your models — you didn't write any HTML or forms for it. Given a model like `KnowledgeBase` in `models.py`, registering it in `admin.py` gets you for free:

- **Read** — a list page (`list_display` controls which columns show) and filters (`list_filter`)
- **Create** — an "Add" form with a field per model attribute
- **Update** — click a row, edit fields, save
- **Delete** — delete button/action on rows

So for `Document`, you get a working admin page to browse all uploaded PDFs, filter by `status`/`knowledge_base`, and edit or delete them — without writing a single template or form by hand. That's the trade-off of Django admin: fast to stand up, but it's an internal/staff tool, not meant to be the product's user-facing UI (that's what the Angular frontend and the `/api/` DRF endpoints are for).

---

## What do you mean by "auto-generated" from the models

It means Django inspects the Python model *class definition* — the field types you already declared — and builds forms/tables from that metadata at runtime, rather than you writing HTML/forms by hand for each one.

Take `models.py`:

```python
class KnowledgeBase(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Each field's Python type tells Django everything it needs to render an admin form:
- `CharField(max_length=255)` → a single-line text `<input>` capped at 255 chars, with a `required` HTML attribute (since it's not `blank=True`)
- `SlugField` → same, but validated against the slug pattern (letters/numbers/hyphens)
- `TextField` → a `<textarea>`
- `DateTimeField(auto_now_add=True)` → **excluded from the form entirely**, since `auto_now_add` means Django sets it itself on creation — it shows as read-only in the list/detail view

You never wrote a `<form>`, an `<input type="text">`, or a validation rule for "name must be ≤255 chars" — that logic lives once, in the model, and both the database schema *and* the admin UI derive from it. That's the "auto" part: one source of truth (the model), multiple things generated from it (DB table via migrations, admin form via `ModelAdmin`, and — if you used DRF's `ModelSerializer` the same way — the API's JSON shape too, as seen in `serializers.py`).

The bare minimum to get this is just:
```python
admin.site.register(KnowledgeBase)
```
That alone gives you a full CRUD page. What `admin.py` actually does is layer customization on top of the auto-generated defaults — `list_display` picks which fields show as table columns (default would be just `__str__`), `list_filter` adds a sidebar, `prepopulated_fields = {"slug": ("name",)}` makes the slug field auto-fill via JS as you type the name. You're tweaking the generated UI, not building it from scratch.

Contrast that with the Angular frontend: `document-upload.component.ts` presumably has hand-written form fields, validation, and API calls — because that's a bespoke UI for end users. The admin is the opposite: zero-effort scaffolding meant for internal/staff use, traded off against control over look-and-feel.
