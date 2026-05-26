---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - c:\Users\cresp\Documents\Projectos\FamFin-AI\_bmad-output\planning-artifacts\product_brief_famfin_ai.md
  - c:\Users\cresp\Documents\Projectos\FamFin-AI\_bmad-output\planning-artifacts\prd.md
workflowType: 'architecture'
project_name: 'FamFin-AI'
user_name: 'Tony'
date: '2026-05-09'
lastStep: 8
status: 'complete'
completedAt: '2026-05-09'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- **Asynchronous Messaging Gateway (n8n):** The system must handle real-time webhooks from Telegram and WhatsApp, manage Meta's media download APIs, and route text/audio payloads to the FastAPI core.
- **Dual-AI Pipeline:** Integration of Faster-Whisper for Speech-to-Text and Ollama for structured JSON extraction (Amount, Category, Concept) within the secure FastAPI app.
- **Conversational Query Logic:** A natural language query engine to handle the "ASK" functionality.
- **Multi-tenant Ledger:** A database schema designed around "Family" units for data isolation.
- **Silent Mirroring (n8n):** An n8n workflow system to synchronize local records with Notion databases for premium users.

**Non-Functional Requirements:**
- **Performance (The Hard Constraint):** The 3-second rule requires extreme optimization of the AI pipeline.
- **Data Sovereignty:** Absolute requirement for local inference. Data processing cannot be outsourced to external APIs.
- **Encryption at Rest:** Sensitive financial fields must be encrypted using AES-256 before hitting the database.

**Scale & Complexity:**
- Project complexity appears to be: **High**
- Primary technical domain: **Messaging SaaS / AI Engineering / Fintech**
- Estimated architectural components: **6** (Messaging Gateway, AI Orchestrator, PostgreSQL, Notion Sync Worker, Encryption Service, Query Processor)

### Technical Constraints & Dependencies
- **Hardware Bottleneck:** Initial deployment restricted to a single local machine for up to 10 users.
- **Containerization:** Use Podman for local container management for future portability.

### Cross-Cutting Concerns Identified
- **Pipeline Performance Monitoring:** Instrumented tracing for every stage (STT -> LLM -> DB).
- **Tenant Scoping:** Universal middleware for `family_id` filtering.
- **Encryption Utility:** Standardized service for transparent field-level encryption/decryption.

## Starter Template Evaluation

### Primary Technology Domain

**High-Performance AI Backend (FastAPI)** based on the requirement for real-time local AI processing and asynchronous messaging.

### Starter Options Considered

1.  **FastAPI Full Stack (Tiangolo):** Evaluated for its robustness but rejected due to excessive frontend overhead (React/Vue) not required for the messaging-first MVP.
2.  **NestJS (TypeScript):** Evaluated for its enterprise structure but rejected in favor of Python for better native integration with Ollama and Faster-Whisper.
3.  **FastAPI + n8n Hybrid Gateway (Selected):** A modular architecture combining self-hosted n8n (Community Edition) for channel connections and Notion integration, alongside a core FastAPI backend for secure local AI processing, multi-tenant databases, and field-level encryption.

### Selected Starter: Modular FastAPI + n8n Blueprint

**Rationale for Selection:**
This hybrid approach provides the absolute fastest speed-to-market for Telegram and WhatsApp webhooks via n8n's visual node orchestrator, while preserving the strict privacy, performance, and field-level database encryption managed inside our secure, compiled FastAPI Python backend.

**Initialization Command:**

```bash
pip install fastapi[all] sqlmodel cryptography ollama faster-whisper python-telegram-bot
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python 3.10+ using FastAPI for non-blocking asynchronous I/O.

**Styling Solution:**
N/A (Messaging interface primarily).

**Build Tooling:**
Podman + Podman Compose for container orchestration and environment isolation.

**Testing Framework:**
Pytest for unit and integration testing of the AI extraction pipeline.

**Code Organization:**
"Service Layer" pattern separating API logic, AI inference (services), and Database access.

**Development Experience:**
FastAPI auto-generated Swagger UI and Uvicorn hot-reloading.

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- **Data Privacy:** Application-Level AES-256 Encryption (FastAPI handles encryption inside Python before writing to Postgres).
- **Inference Engine:** Ollama (LLM) and Faster-Whisper (STT) for local execution via Python service wrappers.
- **Messaging Router:** Self-hosted n8n (Community Edition) to handle WhatsApp Cloud API and Telegram Webhook ingestion.
- **Async Strategy:** FastAPI `BackgroundTasks` for non-blocking 3s confirmation loops.

**Important Decisions (Shape Architecture):**
- **Multi-Tenancy:** Shared schema with `family_id` scoping and row-level filtering.
- **ORM:** SQLModel for unified Pydantic/SQLAlchemy modeling.
- **Authentication:** Telegram and WhatsApp User IDs mapped to `User` and `Family` tables, routed and verified via n8n/FastAPI payload tokens.

**Deferred Decisions (Post-MVP):**
- **Distributed Workers:** Migration to Celery/Redis deferred until Phase 2 scaling (>10 users).
- **Web Dashboard:** Full React/Next.js frontend deferred to Phase 3.

### Data Architecture

- **Database:** PostgreSQL (v16+) via SQLModel.
- **Encryption:** `cryptography` (Python library) using Fernet (AES-256) for field-level masking.
- **Multi-Tenancy:** Single database, single schema, with a mandatory `family_id` on all financial tables.

### Authentication & Security

- **Identity:** Telegram `user_id` and `chat_id`.
- **Integrity:** HMAC-SHA256 signature verification for all incoming Telegram webhooks.
- **Key Management:** Encryption keys stored as environment variables (loaded into `BaseSettings`).

### API & Communication Patterns

- **API Style:** REST (FastAPI) exposing a secure, internal `/api/v1/message` router to receive standardized message payloads from n8n.
- **Payload Schema:** `{ "user_id": int/str, "channel": "telegram"|"whatsapp", "username": str, "text": str, "audio_url": str }`
- **Asynchrony:** n8n immediately acknowledges incoming webhooks from Meta/Telegram. It then sends a request to FastAPI. FastAPI uses `BackgroundTasks` to orchestrate transcription and extraction and instructs n8n to send the final confirmation message.

### Decision Impact Analysis

**Implementation Sequence:**
1.  Initialize Repository with Podman/FastAPI.
2.  Implement Encryption Utility Service.
3.  Set up SQLModel schemas with `family_id`.
4.  Build the Telegram Webhook handler with signature verification.
5.  Integrate the Faster-Whisper and Ollama orchestrator.

**Cross-Component Dependencies:**
The Encryption Utility is a "Hard Dependency" for the Database layer; no transaction can be written without the encryption service being active.

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Database Naming Conventions:**
- Tables and Columns: `snake_case` (e.g., `user_profiles`, `family_id`).
- Primary Keys: `id` (UUIDv4 suggested).

**API Naming Conventions:**
- Endpoints: `snake_case` (e.g., `/api/v1/get_spending_summary`).
- JSON Keys: `snake_case` (e.g., `{ "transaction_amount": 10.5 }`).

**Code Naming Conventions:**
- Functions/Variables: `snake_case` (PEP8).
- Classes: `PascalCase`.
- Files: `snake_case.py`.

### Structure Patterns

**Project Organization:**
- **Service Layer:** All heavy logic (Ollama, Whisper, Encryption) MUST reside in `services/` classes. API routes are restricted to request validation and service orchestration.
- **Models:** All SQLModel definitions reside in `models/` for centralized schema management.

### Format Patterns

**API Response Formats:**
- **Success:** `{ "status": "success", "data": { ... } }`
- **Error:** `{ "status": "error", "message": "Friendly error", "code": "ERROR_CODE" }`

**Data Exchange Formats:**
- Dates: ISO-8601 strings.
- Booleans: Native JSON `true`/`false`.

### Process Patterns

**Error Handling Patterns:**
- Use custom exception classes (e.g., `InferenceError`) to distinguish between AI failures and system errors.
- Global FastAPI exception handlers to wrap all errors into the standard response format.

**Instrumentation Patterns:**
- **The 3s Audit:** Every AI service call must measure and log its execution time (start/end) to ensure PRD compliance.

### Enforcement Guidelines

**All AI Agents MUST:**
- Use the `EncryptionService` for any field marked as sensitive in the schema.
- Follow the `services/` pattern—never implement business logic inside `main.py`.
- Ensure every database query is filtered by a `family_id` context.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
famfin-ai/
├── docker-compose.yaml      # Multi-container orchestration (FastAPI + Postgres + n8n)
├── .env.example             # Template for Bot Tokens, Encryption Keys, and n8n environment
├── requirements.txt         # Core dependencies (FastAPI, SQLModel, Ollama, etc.)
├── n8n/                     # n8n workflows and configurations
│   └── workflows/           # Backup of JSON configurations for n8n workflows
├── src/
│   ├── main.py              # FastAPI application entry & global exception handlers
│   ├── api/                 # Endpoint logic & request routing
│   │   ├── routes/
│   │   │   ├── message.py   # Standardized endpoint to process message payloads from n8n
│   │   │   ├── queries.py   # The "ASK" query handlers
│   │   │   └── family.py    # Family management (Phase 2)
│   │   └── deps.py          # FastAPI Dependables (Current Family Context, DB Session)
│   ├── core/                # Cross-cutting system logic
│   │   ├── config.py        # Pydantic Settings (Environment validation)
│   │   ├── security.py      # Internal webhook security verification
│   │   └── encryption.py    # AES-256 Application-level encryption service
│   ├── services/            # Implementation of the "Inference Pipeline"
│   │   ├── ai_orchestrator.py # Manages the 3s STT -> LLM flow
│   │   ├── whisper_service.py # Faster-Whisper wrapper
│   │   ├── extraction_service.py # Ollama LLM wrapper (JSON Mode)
│   │   └── notion_mirror.py   # Notion mirroring logic (Phase 2)
│   └── db/
│       ├── session.py       # SQLAlchemy engine & session factory
│       └── models.py        # Unified SQLModel schemas (User, Transaction, Family)
├── tests/                   # Performance and Accuracy auditing
│   ├── api/                 # Endpoint integration tests
│   ├── services/            # AI Extraction accuracy benchmarks (The 90% test)
│   └── conftest.py          # Shared test fixtures
└── scripts/
    └── backup_db.py         # Automated local backup routine
```

### Architectural Boundaries

**API Boundaries:**
- The system exposes a single public webhook endpoint for Telegram interaction. 
- Internal boundaries exist between the API routes and the Service layer, ensuring that no raw I/O (like audio processing) blocks the main event loop.

**Component Boundaries:**
- **Inference vs. API:** The AI orchestrator runs in a non-blocking context, allowing the API to return a confirmation to Telegram immediately while processing continues if needed.

**Service Boundaries:**
- **Encryption Service:** Actively isolates the Database from raw PII.
- **AI Services:** Isolate the complexity of Ollama and Faster-Whisper from the business logic.

**Data Boundaries:**
- **Tenant Isolation:** Enforced via a `family_id` on every transaction record.

### Requirements to Structure Mapping

**Feature/Epic Mapping:**
- **Zero-Friction Entry:** `api/routes/logging.py`, `services/whisper_service.py`, `services/extraction_service.py`.
- **"ASK" Queries:** `api/routes/queries.py`, `services/query_service.py`.
- **Privacy Core:** `core/encryption.py`, `db/models.py`.

**Cross-Cutting Concerns:**
- **The 3s Rule Audit:** Instrumented within `services/ai_orchestrator.py`.
- Multi-Tenancy: Handled in `api/deps.py` and `db/models.py`.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
Python 3.10+ serves as the unified runtime for FastAPI, SQLModel, Faster-Whisper, and the Ollama client. Non-blocking I/O is maintained throughout the pipeline.

**Pattern Consistency:**
Strict snake_case is enforced across Code, API, and DB to minimize "translation" logic and reduce mapping bugs.

**Structure Alignment:**
The service-layer pattern (isolating AI and Encryption) ensures that the core application remains testable and scalable.

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**
- **Zero-Friction Entry:** Covered by the asynchronous Whisper/Ollama pipeline.
- **"ASK" Queries:** Supported by a dedicated query service and LLM processing.

**Non-Functional Requirements Coverage:**
- **The 3-Second Rule:** Architecturally prioritized via local inference and async orchestration.
- **Privacy:** Guaranteed by application-level AES-256 encryption and local processing.

### Implementation Readiness Validation ✅

**Decision Completeness:**
All critical technology choices (Framework, AI Engines, DB) are locked with versions and rationale.

**Structure Completeness:**
A comprehensive project directory structure has been defined, mapping features to specific files.

**Pattern Completeness:**
Clear naming conventions and process patterns (like the 3s Audit) are established.

### Gap Analysis Results

- **Prompt Specification (Important):** The exact system prompt for Ollama JSON extraction will be defined during the implementation of the `extraction_service.py`.
- **Key Rotation (Minor):** Master key rotation policy is deferred to Phase 2.

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION
**Confidence Level:** High

**Key Strengths:**
- Extreme focus on latency (The 3s Rule).
- Hardened privacy via local AI and field-level encryption.
- Clean separation of concerns through a service-oriented architecture.

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented.
- Use the standard `snake_case` patterns for all new files and fields.
- Refer to the `Implementation Sequence` for story priority.

**First Implementation Priority:**
Initialize Repository with Podman and FastAPI using the following dependencies:
`pip install fastapi[all] sqlmodel cryptography ollama faster-whisper python-telegram-bot`
