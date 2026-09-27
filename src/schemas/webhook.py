from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class HttpSMSData(BaseModel):
    contact: str = Field(description="The sender's phone number (user asking question)")
    content: str = Field(description="The text message content")
    owner: Optional[str] = Field(default=None, description="The gateway phone number")
    sim: Optional[str] = Field(default=None)
    timestamp: Optional[str] = Field(default=None)
    message_id: Optional[str] = Field(default=None)


class HttpSMSWebhookPayload(BaseModel):
    """httpSMS CloudEvents standard format"""
    type: Optional[str] = Field(default="message.phone.received")
    data: Optional[HttpSMSData] = None
    datacontenttype: Optional[str] = None
    id: Optional[str] = None
    source: Optional[str] = None
    time: Optional[str] = None

    # Fallback flat fields for direct manual curl testing
    contact: Optional[str] = None
    content: Optional[str] = None
    owner: Optional[str] = None
    text: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None


class NormalizedIncomingSMS(BaseModel):
    """Internal canonical representation of an incoming SMS"""
    sender: str
    message: str
    gateway_number: Optional[str] = None


class TestSMSRequest(BaseModel):
    """Direct testing schema for browser/curl testing"""
    phone_number: str = Field(default="+2348000000001", description="Simulated user phone number")
    message: str = Field(..., description="Simulated incoming SMS text")
    language: Optional[str] = Field(default=None, description="Optional override language hint")


class OutgoingSMSRequest(BaseModel):
    """Payload to send to httpSMS REST API"""
    content: str
    from_: str = Field(..., alias="from")
    to: str
