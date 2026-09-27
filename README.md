<div align="center">

# 📡 BeaconSMS (Message Intelligence)
### Bringing Life-Saving AI to the 700+ Million Offline Citizens Across Africa via SMS

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.1-F55036?style=for-the-badge)](https://groq.com)
[![httpSMS](https://img.shields.io/badge/Gateway-httpSMS-blue?style=for-the-badge)](https://httpsms.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<p align="center">
  <b>No Internet. No Smartphone. No Mobile Data.</b><br>
  Instant, life-saving intelligence on any $15 basic feature phone (itel, Tecno, Nokia) over standard 2G cellular SMS.
</p>

[Mission & Research](docs/RESEARCH_AND_IMPACT.md) • [System Architecture](docs/ARCHITECTURE.md) • [Pitch Deck & Demo Guide](docs/PITCH_DECK_GUIDE.md) • [Quickstart](#-quickstart-guide)

</div>

---

## 🌍 The Harsh Reality: Africa's "Usage Gap"

While the developed world accelerates through the Generative AI revolution, **over 60% of Sub-Saharan Africa remains locked out**.

According to the **GSMA Mobile Economy Sub-Saharan Africa 2024 Report** and **ITU Data**:
* **Only 27%** of the population uses mobile internet.
* **The >60% "Usage Gap":** Over **600 million people** live directly under cellular network towers (2G/3G/4G), but **cannot access the internet**.
* **Device Affordability Barrier:** An entry-level smartphone ($50–$90) represents up to 70% of monthly household income. Over **500 million people** rely on $15 basic feature phones for their daily communication.

> Modern AI models live behind data-heavy mobile apps, browser web interfaces, and expensive data subscriptions. **BeaconSMS breaks this digital divide by delivering AI intelligence directly over 2G SMS.**

---

## 💡 Not "Google in Messages" — A Life-Saving Lifeline

BeaconSMS was not built to answer trivia or write essays. It is designed as an **immediate, life-saving, on-time intelligence lifeline**:

```
+---------------------------------------------------------------------------------+
|                                BEACONSMS VERTICALS                              |
+-------------------+--------------------+-------------------+--------------------+
| 🏥 Emergency &    | 🌾 Agriculture &   | 📚 Educational    | 🚨 Disaster &      |
| Healthcare Triage | Food Security      | Equity            | Civic Resilience   |
+-------------------+--------------------+-------------------+--------------------+
| • Infant ORS      | • Fall Armyworm    | • Math & physics  | • Emergency flood  |
|   rehydration     |   pest diagnosis   |   tutoring        |   precautions      |
| • Snakebite first | • Organic neem     | • Mother-tongue   | • Solar & bleach   |
|   aid & burn care |   leaf sprays      |   science lessons |   water purifying  |
| • Maternal labor  | • Drought-tolerant | • Homework help   | • Local epidemic   |
|   warning signs   |   planting cycles  |   without books   |   advisories       |
+-------------------+--------------------+-------------------+--------------------+
```

---

## ⚡ Key Features & Engineering Highlights

* 🧠 **Multi-LLM Engine:** Powered primarily by **Google Gemini 1.5 Flash** for deep multilingual and dialect comprehension. Supports 1-switch fallback to **Groq** (`llama-3.1-8b`, ~280ms latency) and **OpenAI** (`gpt-4o-mini`).
* 🗣️ **Mother-Tongue & Dialect Matching:** Automatically detects and replies in the user's dialect: **Nigerian Pidgin**, **Swahili**, **Yoruba**, **Hausa**, **Igbo**, **French**, or **English**.
* 💬 **Multi-Turn Conversational Memory:** Maintains an in-memory session cache (last 3 conversation turns, 20-minute TTL) keyed by sender phone number. Users can ask natural follow-up questions from a dumb phone!
* 📉 **GSM-7 Character Optimizer:** Automatically strips markdown symbols and normalizes accented Unicode diacritics into plain ASCII. This prevents telecom carriers from dropping into UCS-2 encoding (which shrinks SMS length from 160 chars down to 70 chars).
* ⚡ **Fire-and-Forget Asynchronous Webhooks:** Webhooks return `HTTP 200 OK` in `< 10ms` and process AI generation in an asynchronous background worker, eliminating gateway timeouts and duplicate messages.
* 📱 **Low-Cost Local Gateway:** Runs on an inexpensive spare Android phone with a local SIM card via **httpSMS**, bypassing expensive international SMS aggregators like Twilio.

---

## 🏛️ System Architecture

```
[User's Feature Phone (itel/Nokia)]
       │
       │ 1. Cellular SMS (e.g., "Wetin be first aid for high fever in baby?")
       ▼
[Local Android SIM Gateway (httpSMS Background Service)]
       │
       │ 2. HTTPS Webhook POST (CloudEvents format)
       ▼
[FastAPI Core Backend Engine]
       │ ──> Fast HTTP 200 ACK (< 10ms)
       │
       ├──> Fetch Session Memory (Last 3 turns for this phone)
       ├──> Query Google Gemini / Groq with Character Constraints
       ├──> Sanitize Markdown & Normalize ASCII (GSM-7 preservation)
       ├──> Cache Conversation Turn
       │
       │ 3. HTTPS REST API (POST /v1/messages/send)
       ▼
[Local Android SIM Gateway]
       │
       │ 4. Cellular SMS Reply
       ▼
[User's Feature Phone gets clear, life-saving advice in 5–7 seconds!]
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.10+
* An Android phone with a working SIM card and active SMS bundle
* An account on [httpsms.com](https://httpsms.com) (free)
* A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/)) or Groq API key ([Groq Console](https://console.groq.com/))

### 2. Setup the Android Gateway Phone
1. Install the **httpSMS APK** onto the Android phone from the [httpSMS GitHub](https://github.com/NdoleStudio/httpsms/releases).
2. Log into the app with your API key from [httpsms.com/settings](https://httpsms.com/settings).
3. In Android Settings $\rightarrow$ Battery $\rightarrow$ **Disable Battery Optimization** for httpSMS.
4. Send a test SMS from another phone to confirm the message appears in your httpSMS dashboard.

### 3. Clone & Configure the Backend
```bash
git clone https://github.com/yourusername/beacon-sms.git
cd beacon-sms

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
```

Edit your `.env` file:
```env
HTTPSMS_API_KEY=your_httpsms_api_key_here
GATEWAY_PHONE_NUMBER=+2348000000000
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Server
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Test health endpoint:
```bash
curl http://localhost:8000/health
```

### 5. Expose Webhook to the World
Use **ngrok** to create a public URL:
```bash
ngrok http 8000
```
Copy your forward URL (e.g. `https://xyz.ngrok-free.app`) and configure it in your [httpSMS Webhooks Dashboard](https://httpsms.com/webhooks):
* **Event:** `message.phone.received`
* **URL:** `https://xyz.ngrok-free.app/webhook`

---

## 🧪 Testing Locally (Without an Android Phone)

You can test the entire AI prompt, dialect detection, and character budgeting without a physical SIM card using the built-in testing endpoint:

```bash
curl -X POST http://localhost:8000/test-sms \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+2348011223344",
    "message": "My baby dey stool water water, how I fit prepare salt and sugar solution?"
  }'
```

**Sample Output:**
```json
{
  "user_phone": "+2348011223344",
  "input_message": "My baby dey stool water water, how I fit prepare salt and sugar solution?",
  "sms_reply": "Mix 1 litre clean boiled water with 6 level teaspoons sugar and half level teaspoon salt. Stir well. Give baby small sips frequently. If vomiting persists or baby is weak, take them to clinic immediately.",
  "character_count": 218,
  "sms_segments_estimate": 2,
  "provider": "gemini"
}
```

---

## 🚢 Production Cloud Deployment

### 1-Click Deploy on Render
Connect your GitHub repository to [Render.com](https://render.com) using the included `render.yaml` blueprint.

### Docker Deployment
```bash
docker-compose up --build -d
```

---

## 📈 Roadmap: From Prototype to 100M Scale

* [x] **Phase 1 (Hackathon MVP):** Android SIM gateway + Google Gemini 1.5 Flash + multi-dialect prompt engine + conversation memory.
* [ ] **Phase 2 (Telco Aggregator Integration):** Connect directly to **Africa's Talking** and **Twilio 2-Way Local Shortcodes** for 1,000+ msg/sec carrier capacity.
* [ ] **Phase 3 (Toll-Free Government Shortcodes):** Deploy reverse-billed shortcodes (e.g., `*384#` or `7000`) sponsored by health ministries, UNICEF, and agriculture extension agencies so citizens pay zero airtime.

---

## 📚 Detailed Documentation
* 📑 [Research & Social Impact Paper](docs/RESEARCH_AND_IMPACT.md)
* 📐 [Technical Architecture & Encoding Specs](docs/ARCHITECTURE.md)
* 🎤 [Pitch Deck & Live Demo Script](docs/PITCH_DECK_GUIDE.md)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
