"""
SMS Service: Dispatches outbound SMS messages via the httpSMS REST API.
Includes automatic failover to a secondary backup phone number and simulation mode.
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

    async def _dispatch_single(self, to_phone: str, content: str, sender: str) -> Dict[str, Any]:
        """Dispatches an outbound SMS payload to the httpSMS endpoint."""
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
                logger.info(f"Successfully dispatched SMS from {sender} to {to_phone}. Response ID: {data.get('data', {}).get('id')}")
                return {"status": "sent", "response": data, "sender_used": sender}
            except httpx.HTTPStatusError as e:
                logger.error(f"httpSMS API error from {sender}: {e.response.status_code} - {e.response.text}")
                return {"status": "error", "code": e.response.status_code, "detail": e.response.text, "sender_used": sender}
            except Exception as e:
                logger.error(f"Failed to communicate with httpSMS API from {sender}: {e}")
                return {"status": "failed", "error": str(e), "sender_used": sender}

    async def send_sms(self, to_phone: str, content: str, from_phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends an outbound SMS message with automatic failover to the secondary backup number.
        """
        primary_sender = from_phone or self.default_gateway
        result = await self._dispatch_single(to_phone, content, primary_sender)

        # Automatic failover if primary dispatch fails and a secondary backup is configured
        backup_sender = settings.secondary_phone_number
        if result.get("status") in ("error", "failed") and backup_sender and backup_sender != primary_sender:
            logger.warning(
                f"Primary dispatch via {primary_sender} failed ({result.get('status')}). "
                f"Executing automatic failover to backup gateway: {backup_sender}..."
            )
            failover_result = await self._dispatch_single(to_phone, content, backup_sender)
            if failover_result.get("status") == "sent":
                logger.info(f"Failover successful via backup gateway {backup_sender}!")
                return failover_result

        return result


# Singleton instance
sms_service = SMSService()
