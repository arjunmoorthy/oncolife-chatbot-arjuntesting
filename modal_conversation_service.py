import json
import uuid
from typing import Dict, Any, List, Tuple, AsyncGenerator, Generator
from datetime import datetime
from models import WebSocketMessageIn, WebSocketMessageOut, ProcessResponse, ConversationUpdate, Message
from constants import ConversationState
from llm.gpt import GPT4oProvider
from llm.context import ContextLoader

# Mock database models for Modal deployment
class ChatModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    uuid = None
    patient_uuid = None
    conversation_state = None
    symptom_list = None

class MessageModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    id = None
    chat_uuid = None
    sender = None
    message_type = None
    content = None
    structured_data = None

class ModalConversationService:
    """Modal-compatible version of ConversationService with in-memory storage."""
    
    def __init__(self):
        self.conversations = {}  # In-memory conversation storage
        self.llm_provider = GPT4oProvider()
        self.context_loader = ContextLoader("model_inputs")
    
    def _get_or_create_conversation(self, chat_uuid: str) -> ChatModel:
        """Get existing conversation or create a new one."""
        if chat_uuid not in self.conversations:
            self.conversations[chat_uuid] = ChatModel(
                uuid=chat_uuid,
                patient_uuid=str(uuid.uuid4()),
                conversation_state=ConversationState.CHEMO_CHECK_SENT,
                symptom_list=[]
            )
        return self.conversations[chat_uuid]
    
    def _determine_next_state_and_response(self, chat: ChatModel, message: WebSocketMessageIn) -> Tuple[str, WebSocketMessageOut]:
        """The main state machine for the conversation - EXACT same logic as production."""
        current_state = chat.conversation_state
        next_state = current_state
        response_content = "I'm not sure how to respond to that. Can you try again?"
        response_options = []
        response_type = "text"
        
        if current_state == ConversationState.COMPLETED:
            response_content = "This conversation has ended. Please start a new one if you need assistance."
        
        elif current_state == ConversationState.CHEMO_CHECK_SENT:
            # User responded to "Did you get chemotherapy today?"
            user_response = message.content.lower()
            if user_response in ['yes', 'y', 'true']:
                next_state = ConversationState.SYMPTOM_SELECTION_SENT
                response_content = "Thank you. What symptoms are you experiencing? You can select multiple."
                response_type = "multi_select"
                response_options = [
                    "Fever", "Nausea", "Vomiting", "Diarrhea", "Constipation", "Fatigue",
                    "Headache", "Mouth Sores", "Rash", "Shortness of Breath", "Other"
                ]
            else:
                next_state = ConversationState.COMPLETED
                response_content = "Thank you for letting us know. If you experience any symptoms later, please don't hesitate to reach out."
        
        elif current_state == ConversationState.SYMPTOM_SELECTION_SENT:
            # User selected symptoms
            next_state = ConversationState.SYMPTOM_DETAILS_SENT
            response_content = "I understand you're experiencing these symptoms. Let me ask you some follow-up questions to better understand your situation."
            response_type = "text"
        
        elif current_state == ConversationState.SYMPTOM_DETAILS_SENT:
            # User provided symptom details
            next_state = ConversationState.RECOMMENDATION_SENT
            response_content = "Based on your symptoms, here are some recommendations. However, please consult your healthcare provider for medical advice."
            response_type = "text"
        
        elif current_state == ConversationState.RECOMMENDATION_SENT:
            # User acknowledged recommendations
            next_state = ConversationState.COMPLETED
            response_content = "Thank you for using OncoLife. Remember to contact your healthcare team if your symptoms worsen or you have concerns."
        
        # Update conversation state
        chat.conversation_state = next_state
        
        return next_state, WebSocketMessageOut(
            type="assistant_message",
            content=response_content,
            message_type=response_type,
            options=response_options
        )
    
    async def process_message(self, chat_uuid: str, message: WebSocketMessageIn) -> ProcessResponse:
        """Process a message and return the response - EXACT same logic as production."""
        # Get or create conversation
        chat = self._get_or_create_conversation(chat_uuid)
        
        # Create user message with proper mock ID
        user_msg = MessageModel(
            id=1,  # Mock ID
            chat_uuid=chat_uuid,
            sender="user",
            message_type="text",
            content=message.content,
            structured_data=message.structured_data
        )
        
        # Determine next state and response
        next_state, response = self._determine_next_state_and_response(chat, message)
        
        # Create assistant message with proper mock ID
        assistant_msg = MessageModel(
            id=2,  # Mock ID
            chat_uuid=chat_uuid,
            sender="assistant",
            message_type=response.message_type,
            content=response.content,
            structured_data={"options": response.options} if response.options else None
        )
        
        # Return the response in the same format as production
        return ProcessResponse(
            user_message_saved=Message.from_orm(user_msg),
            assistant_response=Message.from_orm(assistant_msg),
            conversation_updated=ConversationUpdate(new_state=next_state, symptom_list=chat.symptom_list)
        ) 