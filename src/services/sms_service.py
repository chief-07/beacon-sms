"""
SMS Service: Dispatches outbound SMS messages via the httpSMS REST API.
Includes automatic failover to a secondary backup phone number and simulation mode.
"""

import asyncio
import httpx
import logging
import re
from typing import Optional, Dict, Any, List

from src.config import settings

logger = logging.getLogger(__name__)

HTTPSMS_API_URL = "https://api.httpsms.com/v1/messages/send"


def split_into_sms_segments(text: str, max_len: int = 160) -> List[str]:
    """
    Splits text into standalone SMS segments (<= max_len characters).
    Avoids multi-part concatenation (CSMS) UDH headers that cause delivery delays on carrier networks.
    If text > max_len, prefixes with (1/2), (2/2) etc. and splits cleanly at sentence or word boundaries.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_len:
        return [text]

    max_part_payload = max_len - 6  # Reserve 6 chars for prefix like "(1/2) "

    # For 2-part messages (up to ~308 chars), attempt clean sentence or word boundary split
    if len(text) <= max_part_payload * 2:
        min_split = max(1, len(text) - max_part_payload)
        max_split = min(len(text), max_part_payload)

        best_split = -1
        # Try sentence boundary (. ! ?)
        for i in range(max_split, min_split - 1, -1):
            if text[i - 1] in ('.', '!', '?') and (i == len(text) or text[i] in (' ', '\n')):
                best_split = i
                break

        # Fallback to word boundary
        if best_split == -1:
            for i in range(max_split, min_split - 1, -1):
                if text[i] == ' ':
                    best_split = i
                    break

        if best_split != -1:
            part1 = text[:best_split].strip()
            part2 = text[best_split:].strip()
            return [f"(1/2) {part1}", f"(2/2) {part2}"]

    # General N-part word-boundary split for longer messages
    words = text.split(' ')
    raw_parts = []
    current_words = []
    current_len = 0

    for word in words:
        if not word:
            continue
        add_len = len(word) + (1 if current_words else 0)
        if current_len + add_len <= max_part_payload:
            current_words.append(word)
            current_len += add_len
        else:
            if current_words:
                raw_parts.append(" ".join(current_words))
            current_words = [word]
            current_len = len(word)

    if current_words:
        raw_parts.append(" ".join(current_words))

    total = len(raw_parts)
    return [f"({i}/{total}) {part}" for i, part in enumerate(raw_parts, 1)]


class SMSService:
    def __init__(self):
        self.api_key = settings.httpsms_api_key
        self.secondary_api_key = settings.secondary_httpsms_api_key
        self.default_gateway = settings.gateway_phone_number

    def _get_api_key_for_sender(self, sender: str) -> Optional[str]:
        """Resolves the appropriate API key depending on which gateway SIM is sending."""
        sender_digits = re.sub(r'\D', '', str(sender or ''))
        sec_digits = re.sub(r'\D', '', str(settings.secondary_phone_number or ''))
        
        # If the outbound message is routed through the secondary SIM
        if sec_digits and sender_digits == sec_digits and self.secondary_api_key:
            return self.secondary_api_key
        
        return self.api_key or self.secondary_api_key

    async def _dispatch_single(self, to_phone: str, content: str, sender: str) -> Dict[str, Any]:
        """Dispatches an outbound SMS payload to the httpSMS endpoint."""
        api_key = self._get_api_key_for_sender(sender)
        if not api_key or api_key in ("your_httpsms_api_key_here", "your_secondary_httpsms_api_key_here"):
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
            "x-api-key": api_key,
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
        If content > 160 characters and sms_split_long_messages is enabled,
        splits into standalone single-segment messages dispatched with a pacing delay.
        """
        segments = [content]
        if settings.sms_split_long_messages and len(content) > 160:
            segments = split_into_sms_segments(content, max_len=160)
            logger.info(f"Splitting {len(content)}-character message into {len(segments)} standalone SMS segments")

        primary_sender = from_phone or self.default_gateway
        backup_sender = settings.secondary_phone_number
        dispatched_results = []

        for idx, segment in enumerate(segments):
            if idx > 0 and settings.sms_segment_delay_seconds > 0:
                logger.info(
                    f"Pacing delay ({settings.sms_segment_delay_seconds}s) before dispatching segment {idx + 1}/{len(segments)}..."
                )
                await asyncio.sleep(settings.sms_segment_delay_seconds)

            res = await self._dispatch_single(to_phone, segment, primary_sender)

            # Automatic failover if primary dispatch fails and a secondary backup is configured
            if res.get("status") in ("error", "failed") and backup_sender and backup_sender != primary_sender:
                logger.warning(
                    f"Primary dispatch via {primary_sender} failed for segment {idx + 1} ({res.get('status')}). "
                    f"Executing automatic failover to backup gateway: {backup_sender}..."
                )
                failover_res = await self._dispatch_single(to_phone, segment, backup_sender)
                if failover_res.get("status") == "sent":
                    logger.info(f"Failover successful via backup gateway {backup_sender} for segment {idx + 1}!")
                    res = failover_res

            dispatched_results.append(res)

        if len(dispatched_results) == 1:
            return dispatched_results[0]

        all_sent = all(r.get("status") in ("sent", "simulated") for r in dispatched_results)
        return {
            "status": "sent" if all_sent else "partial_error",
            "segments_count": len(dispatched_results),
            "results": dispatched_results,
            "sender_used": primary_sender
        }


# Singleton instance
sms_service = SMSService()
