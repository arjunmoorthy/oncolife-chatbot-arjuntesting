from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class TestChatMessage(BaseModel):
    message: str
    sender: str = Field(default="bot")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: str = Field(default="text")
    options: Optional[List[str]] = Field(default=None)

class TestChatRequest(BaseModel):
    message: str
    chat_uuid: str = Field(default="test-chat") 