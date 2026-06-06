# FamFin-AI 💰🤖

FamFin-AI is a privacy-first, multi-tenant family financial assistant. It features a high-performance FastAPI backend, a local-first AI pipeline for voice-to-JSON expense tracking, and application-level encryption to ensure data privacy.

## 🚀 Quick Start

### 1. Prerequisites
- **Podman** & **Podman Compose** installed.
- Python 3.12+ (optional, for local development).

### 2. Environment Setup
Copy the example environment file and configure your secrets:
```bash
cp .env.example .env
```

### 3. Generate Encryption Key
The project uses application-level AES-128 encryption via the Fernet recipe. You **must** generate a valid key for your `.env` file:
```bash
# Using the provided helper script
python scripts/generate_key.py
```
Copy the output into `ENCRYPTION_KEY` in your `.env`.

### 4. Launch the Application
Start the containerized environment (FastAPI + PostgreSQL + n8n + Ollama):
```bash
podman compose up -d --build
```

- **FastAPI API:** [http://localhost:8000](http://localhost:8000)
- **n8n Workflow Engine:** [http://localhost:5678](http://localhost:5678)
- **Ollama AI Inference:** [http://localhost:11434](http://localhost:11434)

### 5. Download AI Models
To prepare the system for transaction extraction and speech-to-text:
```bash
# Pull the lightweight LLM for transaction parsing
podman compose exec ollama ollama pull gemma:2b
```

---

## 🔗 n8n Webhook Integration

To connect n8n with the FastAPI backend:
1. Configure n8n to send parsed Telegram/WhatsApp payloads to `POST http://app:8000/api/v1/messages`.
2. Include the authentication header:
   * **Header Name:** `X-FamFin-Token`
   * **Header Value:** The secret value you configured for `MESSAGING_WEBHOOK_SECRET` in your `.env` file.

---

## 🛠 Development Commands

### Check Application Health
Verify the API and Database connectivity:
```bash
curl http://localhost:8000/health
```

### Run Tests
All unit and integration tests should be run inside the container to ensure environment parity:
```bash
podman compose exec app pytest
```

### View Logs
```bash
podman compose logs -f app
```

---

## 🏗 Project Architecture

- **`src/`**: Core application logic.
  - **`core/`**: Security (Encryption), Configuration, and Shared Utilities.
  - **`db/`**: SQLModel sessions and database initialization.
  - **`api/`**: FastAPI routers and endpoints.
- **`tests/`**: Pytest suite organized by service and layer.
- **`scripts/`**: Development and maintenance utilities.
- **`_bmad-output/`**: Project planning, architecture, and sprint tracking artifacts.

## 🔒 Security Principles
- **Field-Level Encryption**: Sensitive financial data is encrypted before storage using `cryptography.fernet`.
- **Multi-Tenancy**: Data is strictly isolated per family/user using a multi-tenant schema.
- **Local AI**: Voice processing (Faster-Whisper) and extraction (Ollama) run locally to keep data off the public cloud.

---

## 📅 Sprint Status
The project progress is tracked in `_bmad-output/implementation-artifacts/sprint-status.yaml`.
**Epic 1: Privacy-First Foundation** is completed. Ready to begin **Epic 2: Zero-Friction Expense Logging**.
