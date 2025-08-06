from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ChatMessage:
    content: str
    role: str
    chat_uuid: str
    timestamp: Optional[datetime] = None

@dataclass
class ChatResponse:
    content: str
    timestamp: Optional[datetime] = None 