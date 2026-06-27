from pydantic import BaseModel, Field
from typing import Literal, Optional, List

LeadStatus = Literal[
    "new", "engaged", "qualified", "booked", "no_show",
    "follow_up", "not_qualified", "closed_lost", "closed_won"
]

class LeadIn(BaseModel):
    telegram_user_id: str
    telegram_handle: Optional[str] = None
    display_name: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    source_channel: Optional[str] = None
    message_text: str
    thread_id: Optional[str] = None

class LeadContext(BaseModel):
    telegram_user_id: str
    telegram_handle: Optional[str] = None
    display_name: Optional[str] = None
    last_message_text: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    source_channel: Optional[str] = None
    status: LeadStatus = "new"
    score: int = 0
    tags: List[str] = []