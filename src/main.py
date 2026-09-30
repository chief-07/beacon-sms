"""
BeaconSMS - FastAPI Application Entrypoint
A high-throughput, low-latency SMS-to-AI intelligence gateway.
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
import re
from typing import Dict, Any

from src.config import settings
from src.schemas import (
    HttpSMSWebhookPayload,
    NormalizedIncomingSMS,
    TestSMSRequest,
)
from src.services import ai_service, sms_service, memory_service

# Logging configuration
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("beaconsms")

app = FastAPI(
    title="BeaconSMS Gateway",
    description="Life-Saving AI Intelligence over SMS for Feature Phones in Africa",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def process_sms_pipeline(sender: str, message: str, gateway_number: str = None):
    """
    Background worker:
    1. Sends message to AI orchestrator with conversation memory
    2. Receives sanitized, character-budgeted, localized answer
    3. Calls SMS service to dispatch reply to sender's phone
    """
    try:
        logger.info(f"Processing SMS from {sender}: '{message[:40]}...'")
        
        # Generate AI response
        ai_reply = await ai_service.generate_response(
            phone_number=sender,
            user_message=message
        )
        
        logger.info(f"AI response generated ({len(ai_reply)} chars). Dispatching SMS...")

        # Dispatch outbound SMS
        result = await sms_service.send_sms(
            to_phone=sender,
            content=ai_reply,
            from_phone=gateway_number or settings.gateway_phone_number
        )
        logger.info(f"Outbound dispatch result for {sender}: {result.get('status')}")

    except Exception as e:
        logger.error(f"Failed in SMS processing pipeline for {sender}: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    """Health and diagnostic endpoint for cloud liveness probes."""
    return {
        "status": "healthy",
        "service": "BeaconSMS Gateway",
        "version": "1.0.0",
        "llm_provider": settings.llm_provider,
        "max_sms_chars": settings.max_sms_characters,
        "active_sessions": len(memory_service.sessions),
        "gateway_phone": settings.gateway_phone_number or "not-configured",
        "secondary_phone": settings.secondary_phone_number or "not-configured",
        "primary_gateway_active": bool(settings.httpsms_api_key),
        "secondary_gateway_active": bool(settings.secondary_httpsms_api_key),
        "simulation_mode": not bool(settings.httpsms_api_key or settings.secondary_httpsms_api_key)
    }


processed_message_ids = set()


@app.post("/", status_code=status.HTTP_200_OK)
@app.post("/webhook", status_code=status.HTTP_200_OK)
async def incoming_sms_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    httpSMS Webhook Receiver.
    Accepts CloudEvent payloads from the Android Gateway.
    Immediately returns 200 OK (<10ms) and processes the AI generation in the background
    to prevent gateway timeout retries.
    """
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 0. EVENT ROUTING: Process incoming SMS, and log delivery receipts & failures
    event_type = raw_body.get("type")
    if event_type and event_type != "message.phone.received":
        event_data = raw_body.get("data", {}) if isinstance(raw_body.get("data"), dict) else {}
        recipient = event_data.get("contact") or event_data.get("to")
        msg_content = (event_data.get("content") or "")[:40]

        if event_type == "message.phone.delivered":
            logger.info(f"[CARRIER DLR: DELIVERED] Recipient {recipient} received SMS: '{msg_content}...'")
        elif event_type == "message.phone.sent":
            logger.info(f"[RADIO DLR: SENT] Android gateway radio transmitted SMS to {recipient}: '{msg_content}...'")
        elif event_type == "message.send.failed":
            reason = event_data.get("reason") or event_data.get("error") or "Unknown carrier/radio error"
            logger.error(f"[SMS DISPATCH FAILED] Android gateway failed sending to {recipient}. Reason: {reason}")
        else:
            logger.info(f"Ignored non-inbound webhook event: {event_type}")

        return {"status": "ignored", "reason": f"Event '{event_type}' is not an incoming message"}

    # Extract message ID for deduplication
    message_id = None
    if "data" in raw_body and isinstance(raw_body["data"], dict):
        message_id = raw_body["data"].get("message_id") or raw_body["data"].get("id")
    if not message_id:
        message_id = raw_body.get("id")

    if message_id:
        if message_id in processed_message_ids:
            logger.info(f"Ignored duplicate webhook message: {message_id}")
            return {"status": "ignored", "reason": "Duplicate message"}
        processed_message_ids.add(message_id)
        if len(processed_message_ids) > 2000:
            # Prevent unbounded memory growth
            processed_message_ids.pop()

    # Extract sender, message, and owner from CloudEvent format or flat payload
    sender = None
    message = None
    owner = None

    if "data" in raw_body and isinstance(raw_body["data"], dict):
        data = raw_body["data"]
        sender = data.get("contact")
        message = data.get("content")
        owner = data.get("owner")
    else:
        # Fallback for manual/flat JSON testing
        sender = raw_body.get("from") or raw_body.get("contact")
        message = raw_body.get("text") or raw_body.get("content")
        owner = raw_body.get("to") or raw_body.get("owner")

    if not sender or not message:
        logger.warning(f"Ignored webhook missing contact/content: {raw_body}")
        return {"status": "ignored", "reason": "Missing contact or content field"}

    # 1. Clean sender digits
    sender_digits = re.sub(r'\D', '', str(sender))

    # 2. Block Carrier Shortcodes (e.g. 312, 131, 555)
    # Real African mobile numbers have at least 8 to 14 digits (e.g. 080... or +234...)
    if len(sender_digits) < 7:
        logger.warning(f"BLOCKED carrier shortcode message from '{sender}'. No reply will be sent.")
        return {"status": "ignored", "reason": "Carrier shortcode blocked"}

    # 3. Block self-loop (blocks gateway numbers from texting themselves or each other)
    if settings.block_self_loop:
        known_gateways = {
            re.sub(r'\D', '', str(num))
            for num in [settings.gateway_phone_number, settings.secondary_phone_number, owner]
            if num
        }
        if sender_digits in known_gateways:
            logger.warning(f"BLOCKED self-loop message from gateway number '{sender}'.")
            return {"status": "ignored", "reason": "Self-loop blocked"}

    # 4. Block echo of our own system replies
    if message.strip().startswith("Beacon:"):
        logger.info("BLOCKED echo of system message.")
        return {"status": "ignored", "reason": "Echo loop blocked"}

    # Schedule background processing to avoid httpSMS retry loops
    background_tasks.add_task(
        process_sms_pipeline,
        sender=sender,
        message=message,
        gateway_number=owner
    )

    return {
        "status": "queued",
        "message": "SMS received and queued for AI intelligence processing",
        "sender": sender
    }


@app.post("/test-sms")
async def test_sms_synchronous(payload: TestSMSRequest):
    """
    Testing endpoint for developers and hackathon judges.
    Processes the AI pipeline synchronously and returns the generated SMS reply.
    """
    response = await ai_service.generate_response(
        phone_number=payload.phone_number,
        user_message=payload.message
    )

    return {
        "user_phone": payload.phone_number,
        "input_message": payload.message,
        "sms_reply": response,
        "character_count": len(response),
        "sms_segments_estimate": 1 if len(response) <= 160 else 2,
        "provider": settings.llm_provider
    }


@app.delete("/sessions/{phone_number}")
async def reset_session(phone_number: str):
    """Reset conversational memory for a given phone number."""
    memory_service.clear_session(phone_number)
    return {"status": "cleared", "phone_number": phone_number}


# Mount static landing page
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

