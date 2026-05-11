# Product Brief: FamFin AI

**Working Title:** FamFin AI (Family Finance Assistant)
**Focus:** Privacy-First, Family-Centric Financial Tracking via Conversational AI.
**BMAD Compatibility:** High (Modular Architecture, Spec-Driven Invariants).

---

## 1. Project Overview
FamFin AI is a messaging-based (Telegram/WhatsApp) SaaS that allows users to log expenses and manage family budgets using natural language (voice and text). Unlike existing solutions, it prioritizes **data sovereignty** by using local AI models and targets the **family/household segment** through multi-user synchronization.

## 2. Strategic Objectives
- **Zero-Friction Logging:** Enable users to log expenses in <3 seconds via voice or text.
- **Privacy Sovereignty:** Guarantee that financial data and voice recordings never leave the private infrastructure (Zero-Knowledge approach).
- **Family Coordination:** Allow shared visibility of household expenses while maintaining individual privacy controls.
- **Global Scalability:** Build a localized-ready architecture (multi-currency, multilingual) leveraging Estonia e-Residency for international payment processing.

## 3. Core Features
### A. Conversational Engine
- **Natural Language Extraction:** Convert phrases like *"Spent 15k on groceries with credit card"* into structured JSON data.
- **Voice Transcription:** Local processing of .ogg/voice notes using high-accuracy STT models.
- **Conversational Queries:** Answer natural language questions such as *"How much did we spend on fuel this month?"*

### B. Multi-Tenancy & Family Groups
- **Shared Wallets:** Group users into \"Families\" for aggregated reporting.
- **Cross-Member Queries:** Ability to ask about family spending (e.g., *"What was my partner's total spend on clothing?"*).
- **Privacy Toggle:** \"Private Mode\" for specific expenses (e.g., gifts, personal items) to hide them from the family dashboard.

### C. Intelligence & Reporting
- **Visual Insights:** Automated generation of charts (Pie/Bar) sent directly to the chat.
- **Budget Alerts:** Proactive notifications when category limits are reached.

## 4. Technical Stack (The \"Low-Cost/Local\" Stack)
- **Backend:** Python (FastAPI) for AI processing + Node.js (Fastify) for user management/webhooks.
- **Database:** PostgreSQL with Drizzle ORM (Crypted fields for PII).
- **AI Models (Local/Ollama):** 
  - **LLM:** Ollama running Phi-3 or Llama 3.1 (Strict JSON Mode).
  - **STT:** Faster-Whisper (Tiny/Base model).
- **Interface:** Telegram Bot API (MVP), WhatsApp Cloud API (Scale).

## 5. Privacy & Security Invariants (Spec-Driven)
- **GDPR Compliance:** Full adherence to EU data standards via Estonian entity.
- **Data Encryption:** AES-256 encryption for expense descriptions and amounts at rest.
- **Zero-Persistence Audio:** Immediate deletion of voice files after STT processing.
- **Infrastructure:** Self-hosted models to prevent data leakage to 3rd party LLM providers (OpenAI/Google).

## 6. Monetization Strategy
- **Free Tier:** Basic text-only individual tracking (up to 20 logs/month).
- **Premium Individual:** Unlimited voice logging + advanced AI queries + PDF reports.
- **Family Plan:** Multi-user synchronization, shared budgets, and member-level privacy controls.

## 7. Roadmap (BMAD Method)
- **Phase 1 (Discovery):** Define `architecture.md` and `schema.sql` for multi-tenant privacy.
- **Phase 2 (MVP):** Telegram Bot with text-to-JSON extraction (Ollama).
- **Phase 3 (Voice):** Implementation of Whisper for local audio processing.
- **Phase 4 (Social):** Family group logic and shared reporting.
- **Phase 5 (Scale):** WhatsApp integration and Stripe payment gateway.
