<div align="center">

# 📡 BeaconSMS (Message Intelligence)
### Bringing the Multiplicative Power of the Global AI Revolution to Every Hand Across Africa via SMS

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Frontier AI](https://img.shields.io/badge/Frontier%20AI-Google%20%7C%20OpenAI%20%7C%20Groq-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![AI Equity](https://img.shields.io/badge/AI%20Inclusion-Africa%20First-success?style=for-the-badge)](docs/RESEARCH_AND_IMPACT.md)
[![httpSMS](https://img.shields.io/badge/Gateway-httpSMS-blue?style=for-the-badge)](https://httpsms.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<p align="center">
  <b>No Internet. No Smartphone. No Mobile Data.</b><br>
  Plugging the world's most capable frontier AI models directly into standard 2G cellular SMS on any $15 basic feature phone (itel, Tecno, Nokia).
</p>

[The Multiplicative AI Vision](docs/RESEARCH_AND_IMPACT.md) • [System Architecture](docs/ARCHITECTURE.md) • [Pitch Deck & Demo Guide](docs/PITCH_DECK_GUIDE.md) • [Quickstart Guide](#-quickstart-guide)

</div>

---

## 🌟 The Vision: Why Africa Cannot Be Left Behind

Artificial Intelligence is the most potent **multiplicative technology** in human history. It multiplies productivity, democratizes world-class education, solves life-threatening medical triage in rural outposts, and provides enterprise-grade business strategy to village traders.

Yet today, the AI revolution is almost exclusively built for high-speed fiber, 5G networks, and $800 smartphones. 

### The Threat of Exponential Divergence
According to the **GSMA Mobile Economy Sub-Saharan Africa 2024 Report** and **ITU Data**:
* **Only 27%** of Sub-Saharan Africa actively uses mobile internet.
* **The >60% "Usage Gap":** Over **600 million people** live directly under mobile cellular towers, but **cannot afford smartphones or mobile data tariffs**.
* **The Device Reality:** Over **500 million citizens** rely on $15 basic feature phones for their daily communication.

> [!WARNING]
> If modern AI remains locked behind high-bandwidth apps and mobile subscriptions, the historical economic and cognitive gap between Africa and the developed world will not just persist—**it will compound exponentially**.

**BeaconSMS changes the narrative.** We believe access to frontier intelligence is a fundamental human right. By bridging state-of-the-art LLMs with ubiquitous 2G SMS, BeaconSMS ensures that **every African participates in the AI revolution today**, on the devices they already hold in their hands.

---

## 🚀 Access to the Future: The Universal Intelligence Lifeline

BeaconSMS transforms any basic dumb phone into an interactive pocket polymath, opening up the world's knowledge to anyone, anywhere:

```
+---------------------------------------------------------------------------------------------------------+
|                                        BEACONSMS CAPABILITY MATRIX                                      |
+-------------------+--------------------+--------------------+--------------------+----------------------+
| 📚 Education &    | 💼 Commerce &      | 🌾 Agriculture &   | 🏥 Health & Life-  | 🌍 Open Knowledge &  |
| Learning Equity   | Livelihoods        | Food Security      | Saving Triage      | Everyday Life        |
+-------------------+--------------------+--------------------+--------------------+----------------------+
| • Interactive 24/7| • Small business   | • Fall Armyworm    | • Infant ORS       | • Real-time language |
|   math & physics  |   bookkeeping &    |   pest diagnosis   |   rehydration      |   translation        |
|   tutoring        |   pricing models   | • Organic neem     | • Snakebite first  | • Draft business &   |
| • Science concepts| • Market commodity |   leaf sprays      |   aid & burn care  |   official letters   |
|   explained in    |   rate discovery   | • Drought-tolerant | • Maternal labor   | • Civic information, |
|   mother-tongue   | • Micro-enterprise |   planting cycles  |   warning signs    |   rights, & legal    |
|   dialects        |   trade strategies | • Livestock health | • Water sanitation |   processes          |
+-------------------+--------------------+--------------------+--------------------+----------------------+
```

---

## ⚡ Engineering & Technical Highlights

* 🧠 **State-of-the-Art Frontier Multi-LLM Engine:** Connects dynamically to leading AI research labs (Google DeepMind, OpenAI, and Meta/Groq), providing frontier reasoning speed and deep multilingual comprehension.
* 🗣️ **Mother-Tongue & Dialect Matching:** Automatically detects the user's dialect and replies in that exact language: **Nigerian Pidgin**, **Swahili**, **Yoruba**, **Hausa**, **Igbo**, **French**, or **English**.
* 💬 **Multi-Turn Conversational Context:** In-memory session cache maintains the last 3 conversation turns per phone number, allowing natural follow-up questions from any dumb phone.
* 📉 **GSM-7 SMS Encoding Optimizer:** Automatically strips markdown symbols and normalizes accented Unicode diacritics into plain ASCII, ensuring messages stay long (160 chars) and cheap without carrier penalty.
* ⚡ **Ultra-Low Latency (<10ms Webhook ACK):** Non-blocking asynchronous background architecture prevents gateway timeouts and duplicate messages.
* 🛡️ **Intelligent Loop & Shortcode Shield:** Automatically filters out carrier notifications, 3-digit shortcodes (e.g., 312, 131), and self-echo loops.
* 📱 **Frictionless Local Gateway:** Runs on an inexpensive spare Android phone with a local SIM card via **httpSMS**, bypassing expensive international aggregators.

---

## 🏛️ System Architecture

```
[Citizen's Feature Phone (itel/Nokia)]
       │
       │ 1. Cellular SMS (e.g., "Wetin be best way to calculate profit for my small shop?")
       ▼
[Local Android SIM Gateway (httpSMS Background Service)]
       │
       │ 2. HTTPS Webhook POST (CloudEvents format)
       ▼
[FastAPI Core Backend Engine]
       │ ──> Fast HTTP 200 ACK (< 10ms)
       │
       ├──> Inbound Event Filter (Only processes message.phone.received)
       ├──> Fetch Session Memory (Last 3 turns for this phone)
       ├──> Query Frontier AI Models (Google, OpenAI, Groq)
       ├──> Sanitize Markdown & Normalize ASCII (GSM-7 preservation)
       ├──> Cache Conversation Turn
       │
       │ 3. HTTPS REST API (POST /v1/messages/send)
       ▼
[Local Android SIM Gateway]
       │
       │ 4. Cellular SMS Reply
       ▼
[Citizen receives clear, empowering guidance in 5–8 seconds!]
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.10+
* An Android phone with a working SIM card and active SMS bundle
* An account on [httpsms.com](https://httpsms.com) (free)
* An API key from a frontier AI provider (Google AI Studio, Groq, or OpenAI)

### 2. Setup the Android Gateway Phone
1. Install the **httpSMS APK** onto the Android phone from the [httpSMS GitHub](https://github.com/NdoleStudio/httpsms/releases).
2. Log into the app with your API key from [httpsms.com/settings](https://httpsms.com/settings).
3. In Android Settings $\rightarrow$ Battery $\rightarrow$ **Disable Battery Optimization** for httpSMS.
4. Send a test SMS from another phone to confirm the message appears in your httpSMS dashboard.

### 3. Clone & Configure the Backend
```bash
git clone https://github.com/chief-07/beacon-sms.git
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

### 5. Connect Webhook
In your [httpSMS Webhooks Dashboard](https://httpsms.com/webhooks):
* **Event:** `message.phone.received`
* **URL:** `https://your-public-domain.com/webhook` (or Render URL)

---

## 🧪 Testing Locally (Without an Android Phone)

You can test the entire AI prompt, dialect detection, and character budgeting without a physical SIM card using the built-in testing endpoint:

```bash
curl -X POST http://localhost:8000/test-sms \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+2348011223344",
    "message": "Explain how photosynthesis works in Nigerian Pidgin in two short sentences."
  }'
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

* [x] **Phase 1 (Hackathon MVP):** Android SIM gateway + Frontier AI engine + multi-dialect prompt engine + conversation memory + loop protection.
* [ ] **Phase 2 (Telco Aggregator Integration):** Connect directly to **Africa's Talking** and **Twilio 2-Way Local Shortcodes** for 1,000+ msg/sec carrier capacity.
* [ ] **Phase 3 (Toll-Free Government Shortcodes):** Deploy reverse-billed shortcodes (e.g., `*384#` or `7000`) sponsored by education ministries, health agencies, and UNESCO so citizens pay zero airtime.

---

## 📚 Detailed Documentation
* 📑 [Research & The Multiplicative AI Vision](docs/RESEARCH_AND_IMPACT.md)
* 📐 [Technical Architecture & Encoding Specs](docs/ARCHITECTURE.md)
* 🎤 [Pitch Deck & Live Demo Script](docs/PITCH_DECK_GUIDE.md)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
