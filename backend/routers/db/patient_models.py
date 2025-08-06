"""
Mock Database Models for Standalone Chatbot

These are simplified versions of the database models that the services expect.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional

class Conversations:
    """Mock Conversations model"""
    def __init__(self, **kwargs):
        self.uuid = kwargs.get('uuid', UUID('12345678-1234-5678-1234-567812345678'))
        self.patient_uuid = kwargs.get('patient_uuid')
        self.conversation_state = kwargs.get('conversation_state', 'CHEMO_CHECK_SENT')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

class Messages:
    """Mock Messages model"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.chat_uuid = kwargs.get('chat_uuid')
        self.sender = kwargs.get('sender', 'assistant')
        self.message_type = kwargs.get('message_type', 'text')
        self.content = kwargs.get('content', '')
        self.structured_data = kwargs.get('structured_data', {})
        self.created_at = kwargs.get('created_at', datetime.now()) 