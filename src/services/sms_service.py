"""
SMS Service: Dispatches outbound SMS messages via the httpSMS REST API.
Includes simulation mode when running without an active Android gateway.
"""

import httpx
import logging
from typing import Optional, Dict, Any

from src.config import settings

logger = logging.getLogger(__name__)

HTTPSMS_API_URL = "https://api.httpsms.com/v1/messages/send"


class SMSService:
    def __init__(self):
        self.api_key = settings.httpsms_api_key
        self.default_gateway = settings.gateway_phone_number

    async def send_sms(self, to_phone: str, content: str, from_phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends an outbound SMS message via httpSMS.
        Falls back to simulation mode if API key is not configured.
        """
        sender = from_phone or self.default_gateway

        if not self.api_key or self.api_key == "your_httpsms_api_key_here":
            logger.info(
                f"[SIMULATION MODE] Would send SMS:\n"
                f"  To: {to_phone}\n"
                f"  From: {sender}\n"
                f"  Length: {len(content)} chars\n"
                f"  Content: {content}"
            )
            return {
                "status": "simulated",
                "to": to_phone,
                "from": sender,
                "content": content,
                "length": len(content)
            }

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "content": content,
            "from": sender,
            "to": to_phone
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(HTTPSMS_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successfully dispatched SMS to {to_phone}. Response ID: {data.get('data', {}).get('id')}")
                return {"status": "sent", "response": data}
            except httpx.HTTPStatusError as e:
                logger.error(f"httpSMS API error: {e.response.status_code} - {e.response.text}")
                return {"status": "error", "code": e.response.status_code, "detail": e.response.text}
            except Exception as e:
                logger.error(f"Failed to communicate with httpSMS API: {e}")
                return {"status": "failed", "error": str(e)}


# Singleton instance
sms_service = SMSService()
