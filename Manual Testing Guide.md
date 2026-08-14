# Complete Manual Testing Guide: FamFin-AI (Zero to Telegram)

This guide walks you through building, configuring, and testing the **FamFin-AI** system from complete scratch (zero state) using **Podman** and **Telegram**.

---

## 🏗️ Architecture & Pipeline Overview

```
[ Telegram User ] (Text or Voice)
       │
       ▼
   [ n8n ] (Telegram Trigger Workflow)
       │  (Resolves Voice URL if audio / Extracts text)
       ▼  POST http://app:8000/messages (Header: x-famfin-token)
 [ FamFin API ] ── Immediate 200 OK (< 3s)
       │
       ├─► (Background Task)
       │      │
       │      ├─► [ Faster-Whisper ] (Audio to text transcription)
       │      ├─► [ Ollama - Llama3 ] (JSON extraction: Amount, Concept, Category)
       │      └─► [ PostgreSQL ] (AES-256 encrypted storage)
       │
       ▼  POST http://n8n:5678/webhook/famfin-callback
   [ n8n ] (Callback Workflow)
       │
       ▼  Telegram "Send Message"
[ Telegram User ] ("Saved $12.50 for 'Lunch' under category 'Food'")
```

---

## Step 1: Prerequisites & Telegram Bot Creation

If you have **nothing set up**, follow these initial steps:

### 1.1 Ensure Podman is Running
On Windows, make sure your Podman machine is running:
```powershell
podman machine start
```
Verify Podman is accessible:
```powershell
podman version
podman-compose --version
```
*(Note: You can use either `podman-compose` or `podman compose`.)*

### 1.2 Create your Telegram Bot
1. Open the Telegram app on your phone or desktop.
2. Search for `@BotFather` and click **Start**.
3. Send the command:
   ```text
   /newbot
   ```
4. Follow the prompts:
   - **Name:** e.g., `My FamFin Assistant`
   - **Username:** e.g., `my_famfin_test_bot` (must end in `bot`)
5. BotFather will provide your **Telegram Bot Token** (e.g., `7123456789:AAF_xxxxxxx_xxxxxxx`).
6. **Save this token** — you will use it in `.env` and n8n.

---

## Step 2: Environment Configuration (`.env`)

1. In the project root (`c:\Users\cresp\Documents\Projectos\FamFin-AI`), copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Generate an AES-256 Fernet encryption key:
   - **Option A (Python script in repo):**
     ```powershell
     python scripts/generate_key.py
     ```
   - **Option B (PowerShell / One-liner):**
     ```powershell
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```

3. Open `.env` and fill in the values:
   ```env
   # Database Configuration
   POSTGRES_USER=famfin_user
   POSTGRES_PASSWORD=famfin_password
   POSTGRES_DB=famfin_db

   # Security & API Keys
   ENCRYPTION_KEY=YOUR_GENERATED_FERNET_KEY_HERE
   TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_FROM_BOTFATHER

   # App Configuration
   DATABASE_URL=postgresql+psycopg://famfin_user:famfin_password@db:5432/famfin_db
   MESSAGING_WEBHOOK_SECRET=famfin_super_secret_webhook_token_123

   # Whisper Settings
   WHISPER_MODEL_SIZE=base
   WHISPER_DEVICE=cpu
   WHISPER_COMPUTE_TYPE=int8

   # Ollama Settings
   OLLAMA_BASE_URL=http://ollama:11434
   OLLAMA_MODEL=llama3

   # Callback URL (n8n container endpoint)
   N8N_CALLBACK_URL=http://n8n:5678/webhook/famfin-callback
   ```

---

## Step 3: Build & Start Containers with Podman

1. Build and start all 4 services (`db`, `app`, `n8n`, `ollama`):
   ```powershell
   podman-compose up -d --build
   ```
   *(or `podman compose up -d --build`)*

2. Verify all containers are running and healthy:
   ```powershell
   podman ps
   ```
   You should see:
   - `famfin-db` (Port `5433->5432`)
   - `famfin-app` (Port `8000->8000`)
   - `famfin-n8n` (Port `5678->5678`)
   - `famfin-ollama` (Port `11434->11434`)

3. Verify API Health:
   Open your browser and navigate to:
   - **Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Step 4: Download Ollama LLM Model

The Ollama container starts without downloaded weights. Pull `llama3` inside the container:

1. Run:
   ```powershell
   podman exec -it famfin-ollama ollama pull llama3
   ```
2. Wait for the download to finish (approx. 4.7 GB).
3. Verify the model is available:
   ```powershell
   podman exec -it famfin-ollama ollama list
   ```

*(Note: Faster-Whisper downloads its `base` model automatically on the first audio request and caches it in the `whisper_model_cache` volume).*

---

## Step 5: n8n Workflow Setup (Telegram Inbound & Outbound)

Open n8n in your browser at: **[http://localhost:5678](http://localhost:5678)**

> **First Time in n8n:** Create your local admin user credentials when prompted.

You will create **two workflows**:
1. **Workflow 1: Telegram Inbound** (Receives text/audio from Telegram -> forwards to FamFin API)
2. **Workflow 2: FamFin Callback** (Receives completed processing from FamFin API -> replies to Telegram)

---

### 5.1 Telegram Inbound Workflow

Create a new workflow named `FamFin Telegram Inbound`:

#### Node 1: Telegram Trigger
1. Add a **Telegram Trigger** node.
2. Under **Credential to connect with**, click *Create New Credential*:
   - Paste your `TELEGRAM_BOT_TOKEN`.
   - Save the credential as `FamFin Telegram Bot`.
3. Set **Updates**: `message`.
4. Click **Listen for Test Event** to confirm connection.

#### Node 2: Code / Function Node (Resolve Audio vs Text)
Add a **Code** node (JavaScript) connected to the Telegram Trigger with the following code:
```javascript
const message = $json.message || {};
const fromUser = message.from || {};
const voice = message.voice;
const botToken = "YOUR_TELEGRAM_BOT_TOKEN_HERE"; // Replace with your token

let audioUrl = null;
let text = message.text || null;

// If voice note was received, resolve the Telegram file download URL
if (voice && voice.file_id) {
  // Telegram File ID is present
  audioUrl = `https://api.telegram.org/bot${botToken}/getFile?file_id=${voice.file_id}`;
}

return {
  json: {
    user: {
      id: fromUser.id,
      username: fromUser.username || null,
      first_name: fromUser.first_name || null,
      last_name: fromUser.last_name || null
    },
    message: {
      message_id: message.message_id,
      chat_id: message.chat ? message.chat.id : fromUser.id,
      text: text,
      voice_file_id: voice ? voice.file_id : null
    }
  }
};
```

#### Node 3: Forward to FamFin API (HTTP Request Node)
Add an **HTTP Request** node connected to Node 2:
- **Method:** `POST`
- **URL:** `http://app:8000/api/v1/messages`
- **Authentication:** `None`
- **Headers:**
  - Name: `x-famfin-token`
  - Value: `famfin_super_secret_webhook_token_123` *(matches `MESSAGING_WEBHOOK_SECRET` in `.env`)*
- **Send Body:** `JSON`
- **Body Parameters (Expression or JSON):**
  ```json
  {
    "user": {{$json.user}},
    "message": {
      "message_id": {{$json.message.message_id}},
      "chat_id": {{$json.message.chat_id}},
      "text": {{$json.message.text}},
      "audio_url": {{$json.message.audio_url}}
    }
  }
  ```

#### Node 4: Reply on `/start` Command (Optional If/Switch node)
If the response from `http://app:8000/messages` returns `action: "reply"`, route to a **Telegram Node** ("Send Message"):
- **Chat ID:** `{{$json.message.chat_id}}`
- **Text:** `{{$json.text}}`

Save and click **Activate Workflow** (toggle at top right).

---

### 5.2 FamFin Callback Workflow (Async Replies to User)

When the backend completes background transcription, extraction, and database persistence, it sends an async POST request to `N8N_CALLBACK_URL` (`http://n8n:5678/webhook/famfin-callback`).

Create a second workflow named `FamFin Callback`:

#### Node 1: Webhook Node
1. Add a **Webhook** node.
2. Set **HTTP Method:** `POST`.
3. Set **Path:** `famfin-callback`.
4. Set **Response Mode:** `When Last Node Finishes` (or `Immediate 200`).

#### Node 2: Telegram Node ("Send Message")
1. Connect the Webhook node to a **Telegram** node.
2. **Resource:** `Message`.
3. **Operation:** `Send Message`.
4. **Chat ID:** `={{ $json.body.chat_id }}`
5. **Text:** `={{ $json.body.text }}`

Save and click **Activate Workflow**.

---

## Step 6: Step-by-Step Testing Scenarios

### 🧪 Test 1: Start Command
1. Open your bot on Telegram.
2. Click **Start** or send:
   ```text
   /start
   ```
3. **Expected Output:**
   Bot immediately replies:
   > *"Welcome to FamFin-AI, [Your Name]! Your account is ready. You can now log your first expense by simply typing it, for example: '50 for lunch' or '100 for groceries'."*

---

### 🧪 Test 2: Text Expense Logging
1. Send a text message in Telegram:
   ```text
   Spent 45.50 on groceries at Walmart
   ```
2. Check backend logs in your terminal:
   ```powershell
   podman logs -f famfin-app
   ```
   You will see:
   ```text
   INFO: ExtractionService: Parsing financial intent...
   INFO: [3s Audit] Total pipeline orchestration took 1.12 seconds
   ```
3. **Expected Output in Telegram:**
   Bot replies:
   > *"Saved 45.50 USD for 'groceries at Walmart' under category 'Food & Groceries'."*

---

### 🧪 Test 3: Voice Note Expense Logging
1. In Telegram, record and send a voice message:
   > 🎙️ *"I paid twenty four dollars and fifty cents for an Uber ride to the airport."*
2. Check backend logs:
   ```powershell
   podman logs -f famfin-app
   ```
   You will see:
   ```text
   INFO: [3s Audit] Whisper transcription took 0.84 seconds ...
   INFO: Extraction completed: amount='24.50', concept='Uber ride to the airport', category='Transport'
   INFO: Encrypted transaction saved to database.
   ```
3. **Expected Output in Telegram:**
   Bot replies:
   > *"Saved 24.50 USD for 'Uber ride to the airport' under category 'Transportation'."*

---

## Step 7: Database & Encryption Verification

Verify that data was stored and encrypted using AES-256:

1. Connect to PostgreSQL inside the Podman container:
   ```powershell
   podman exec -it famfin-db psql -U famfin_user -d famfin_db
   ```

2. Query users:
   ```sql
   SELECT id, telegram_id, username, first_name FROM users;
   ```

3. Query transactions:
   ```sql
   SELECT id, user_id, amount, concept, category, timestamp FROM transactions ORDER BY timestamp DESC LIMIT 5;
   ```
   *Notice that `amount` and `concept` columns contain secure Fernet ciphertext tokens (e.g. `gAAAAAB...`), ensuring zero plaintext leaks at rest.*

4. Exit psql:
   ```sql
   \q
   ```

---

## 🛠️ Troubleshooting & Handy Podman Commands

| Goal | Command |
|---|---|
| View App Logs | `podman logs -f famfin-app` |
| View Ollama Logs | `podman logs -f famfin-ollama` |
| View n8n Logs | `podman logs -f famfin-n8n` |
| Restart App Service | `podman restart famfin-app` |
| Tear down containers | `podman-compose down` |
| Rebuild all containers | `podman-compose up -d --build` |
| Test Ollama Model manually | `podman exec -it famfin-ollama ollama run llama3 "Extract amount: 20 for pizza"` |
