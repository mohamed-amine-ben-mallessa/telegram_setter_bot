from pydantic import BaseModel, Field
from typing import List, Literal, Optional

Intent = Literal[
    "open",
    "qualify",
    "book",
    "follow_up",
    "handoff",
    "close_lost",
    "reactivate"
]

class AIOutput(BaseModel):
    reply_text: str = Field(min_length=1, max_length=600)
    intent: Intent
    status: str
    score_delta: int = Field(ge=-100, le=100)
    next_action: str
    tags: List[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
    short_reason: Optional[str] = None