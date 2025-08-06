"""
Chat and Conversation Routes - Simplified Version

This version removes authentication but keeps all LLM and RAG functionality.
"""

import json
from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status, HTTPException, Query
from typing import List, Optional
from datetime import date

# Import the real services and models
from .models import (
    CreateChatRequest, CreateChatResponse, FullChatResponse, ChatStateResponse, 
    UpdateStateRequest, ChatSummaryResponse, WebSocketMessageIn, TodaySessionResponse,
    Message
)
from .services import ConversationService

router = APIRouter(prefix="/chat", tags=["Chat Conversation"])

# Mock database session for testing
class MockDB:
    def __init__(self):
        self.chats = {}
        self.messages = {}
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass

def get_mock_db():
    return MockDB()

# Mock user for testing
class MockUser:
    def __init__(self):
        self.sub = "test-user-123"
        self.email = "test@example.com"

def get_mock_user():
    return MockUser()

# ===============================================================================
# REST API Routes for Conversation Management
# ===============================================================================

@router.get(
    "/session/today",
    response_model=TodaySessionResponse,
    summary="Get or create the chat session for the current day"
)
def get_or_create_session(
    db = Depends(get_mock_db),
    current_user = Depends(get_mock_user),
    timezone: str = Query(default="America/Los_Angeles", description="User's timezone")
):
    """Get or create today's chat session."""
    conversation_service = ConversationService(db)
    chat, messages, is_new = conversation_service.get_or_create_today_session(
        UUID(current_user.sub), timezone
    )
    
    return TodaySessionResponse(
        data={
            "chat_uuid": str(chat.uuid),
            "conversation_state": chat.conversation_state,
            "messages": [convert_message_for_frontend(msg) for msg in messages],
            "is_new_session": is_new
        }
    )

@router.post(
    "/session/new",
    response_model=TodaySessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Force create a new chat session for the current day"
)
def force_create_new_session(
    db = Depends(get_mock_db),
    current_user = Depends(get_mock_user),
    timezone: str = Query(default="America/Los_Angeles", description="User's timezone")
):
    """Force create a new chat session."""
    conversation_service = ConversationService(db)
    chat, messages, is_new = conversation_service.force_create_today_session(
        UUID(current_user.sub), timezone
    )
    
    return TodaySessionResponse(
        data={
            "chat_uuid": str(chat.uuid),
            "conversation_state": chat.conversation_state,
            "messages": [convert_message_for_frontend(msg) for msg in messages],
            "is_new_session": is_new
        }
    )

def convert_message_for_frontend(message: Message) -> Message:
    """Converts message types from database format to frontend format."""
    if hasattr(message, 'message_type') and isinstance(message.message_type, str):
        message.message_type = message.message_type.replace('_', '-')
    return message

# ===============================================================================
# WebSocket Endpoint
# ===============================================================================

@router.websocket("/ws/{chat_uuid}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_uuid: UUID,
    db = Depends(get_mock_db)
):
    await websocket.accept()
    
    # Send connection established message
    await websocket.send_text(json.dumps({
        "type": "connection_established",
        "chat_state": "CHEMO_CHECK_SENT"
    }))
    
    conversation_service = ConversationService(db)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process the message with real LLM
            async for response in conversation_service.process_message_stream(chat_uuid, message_data):
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        print(f"Client disconnected from chat {chat_uuid}")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
        await websocket.close() 