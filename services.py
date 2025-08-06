import json
import os
from uuid import UUID
from typing import Dict, Any, List, Tuple, AsyncGenerator, Generator
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import date, datetime, time
import pytz

# Absolute imports for Modal
from models import (
    Chat, Message, WebSocketMessageIn, WebSocketMessageOut, 
    ProcessResponse, ConversationUpdate, ConnectionEstablished, WebSocketMessageChunk, WebSocketStreamEnd
)
from constants import ConversationState

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

from llm.gpt import GPT4oProvider
from llm.groq import GroqProvider
from llm.cerebras import CerebrasProvider
from llm.context import ContextLoader

LLM_PROVIDER = "gpt4o"  # Options: "gpt4o", "groq", "cerebras"

def get_llm_provider():
    """Factory function to get the configured LLM provider."""
    if LLM_PROVIDER == "gpt4o":
        return GPT4oProvider()
    elif LLM_PROVIDER == "groq":
        return GroqProvider()
    elif LLM_PROVIDER == "cerebras":
        return CerebrasProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


# ===============================================================================
# Core Conversation Logic (with real database queries)
# ===============================================================================

class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def delete_chat(self, chat_uuid: UUID, patient_uuid: UUID):
        """Deletes a chat conversation after verifying ownership."""
        chat = self.db.query(ChatModel).filter(
            ChatModel.uuid == chat_uuid, 
            ChatModel.patient_uuid == patient_uuid
        ).first()

        if not chat:
            raise ValueError("Chat not found or access denied.")
        
        self.db.delete(chat)
        self.db.commit()
        return

    def create_chat(self, patient_uuid: UUID, commit: bool = True) -> Tuple[ChatModel, Dict[str, Any]]:
        """
        Creates a new chat, saves a system message, and updates the state.
        Can be part of a larger transaction if commit=False.
        """
        # 1. Create the parent Conversation object
        new_chat = ChatModel(
            patient_uuid=patient_uuid,
            conversation_state=ConversationState.CHEMO_CHECK_SENT
        )
        self.db.add(new_chat)
        
        if commit:
            self.db.commit()
            self.db.refresh(new_chat)
            
        initial_question = {
            "text": "Did you get chemotherapy today?",
            "type": "single_select",  # Database format (underscore)
            "frontend_type": "single-select",  # Frontend format (hyphen)
            "options": ["Yes", "No", "I had it recently, but didn't record it"],
        }
        return new_chat, initial_question

    def _determine_next_state_and_response(self, chat: ChatModel, message: WebSocketMessageIn) -> Tuple[str, WebSocketMessageOut]:
        """The main state machine for the conversation."""
        current_state = chat.conversation_state
        next_state = current_state
        response_content = "I'm not sure how to respond to that. Can you try again?"
        response_options = []
        response_type = "text"

        if current_state == ConversationState.COMPLETED:
            response_content = "This conversation has ended. Please start a new one if you need assistance."
        
        elif current_state == ConversationState.CHEMO_CHECK_SENT:
            next_state = ConversationState.SYMPTOM_SELECTION_SENT
            response_content = "Thank you. What symptoms are you experiencing? You can select multiple."
            response_type = "multi_select"
            response_options = [
                "Fever", "Nausea", "Vomiting", "Diarrhea", "Constipation", "Fatigue",
                "Headache", "Mouth Sores", "Rash", "Shortness of Breath", "Other"
            ]

        elif current_state == ConversationState.SYMPTOM_SELECTION_SENT:
            next_state = ConversationState.FOLLOWUP_QUESTIONS
            symptoms = [s.strip() for s in message.content.split(',')]
            chat.symptom_list = list(set((chat.symptom_list or []) + symptoms)) # Append unique symptoms
            self.db.commit()
            
            context = {"patient_state": {"current_symptoms": chat.symptom_list}}
            response_content = self._query_knowledge_base(context)

        elif current_state == ConversationState.FOLLOWUP_QUESTIONS:
            chat_history = self.db.query(MessageModel).filter(MessageModel.chat_uuid == chat.uuid).order_by(MessageModel.id.desc()).limit(20).all()
            context = {
                "patient_state": {"current_symptoms": chat.symptom_list},
                "latest_input": message.content,
                "history": [Message.from_orm(m).model_dump(mode='json') for m in reversed(chat_history)]
            }
            
            llm_response = self._query_knowledge_base(context)

            if "DONE" in llm_response:
                response_content = "DONE"
            else:
                # Check if the LLM is asking the user to add more symptoms
                if "anything else you would like to discuss" in llm_response.lower():
                    response_type = "button_prompt"
                    response_options = ["Yes", "No"]
                
                response_content = llm_response

            next_state = ConversationState.FOLLOWUP_QUESTIONS
        
        assistant_response = WebSocketMessageOut(
            type="assistant_message",
            message_type=response_type,
            content=response_content,
            options=response_options,
        )
        return next_state, assistant_response

    def _summarize_and_complete_chat(self, chat: ChatModel) -> Generator[Any, None, None]:
        """
        Streams a summary to the user, updates the chat, and finalizes the conversation.
        """
        print("Streaming summary and completing chat...")
        
        # 1. Create the final assistant message object in the DB to get an ID
        final_assistant_msg = MessageModel(
            chat_uuid=chat.uuid,
            sender="assistant",
            message_type="text",
            content="", # Start with empty content
        )
        self.db.add(final_assistant_msg)
        self.db.commit()
        self.db.refresh(final_assistant_msg)

        # 2. Yield the initial part of the message to the user first
        initial_summary_text = "You are done with your conversation for today! Here is a brief summary of our conversation:\n"
        yield WebSocketMessageChunk(message_id=final_assistant_msg.id, content=initial_summary_text)

        # 3. Stream the bulleted summary from the LLM
        full_history = self.db.query(MessageModel).filter(MessageModel.chat_uuid == chat.uuid).order_by(MessageModel.id.asc()).all()
        history_text = "\n".join([f"{msg.sender}: {msg.content}" for msg in full_history])
        
        summarization_prompt = (
            "Please analyze the following conversation history and generate ONLY a concise, bulleted summary of the key points."
            f"\n\nConversation History:\n{history_text}"
        )

        llm_provider = get_llm_provider()
        summary_generator = llm_provider.query(system_prompt="You are a clinical summarization assistant.", user_prompt=summarization_prompt)
        
        bulleted_summary = ""
        for chunk in summary_generator:
            bulleted_summary += chunk
            yield WebSocketMessageChunk(message_id=final_assistant_msg.id, content=chunk)

        yield WebSocketStreamEnd(message_id=final_assistant_msg.id)

        # 4. Update the chat object with the final summary and state
        chat.bulleted_summary = bulleted_summary
        chat.conversation_state = ConversationState.COMPLETED
        final_assistant_msg.content = initial_summary_text + bulleted_summary # Save the full text
        self.db.commit()

    def get_or_create_today_session(self, patient_uuid: UUID, user_timezone: str = "America/Los_Angeles") -> Tuple[ChatModel, List[MessageModel], bool]:
        """
        Gets the most recent chat for today, or creates a new one if none exists.
        Uses user's timezone to determine what "today" means.
        """
        # Get today's date in user's timezone
        user_tz = pytz.timezone(user_timezone)
        user_now = datetime.now(user_tz)
        today_start = datetime.combine(user_now.date(), time.min)
        today_end = datetime.combine(user_now.date(), time.max)
        
        # Convert to UTC for database query
        utc_today_start = user_tz.localize(today_start).astimezone(pytz.UTC)
        utc_today_end = user_tz.localize(today_end).astimezone(pytz.UTC)
        
        # Query for today's chat in user's timezone
        today_chat = self.db.query(ChatModel).filter(
            ChatModel.patient_uuid == patient_uuid,
            ChatModel.created_at >= utc_today_start,
            ChatModel.created_at <= utc_today_end
        ).order_by(ChatModel.created_at.desc()).first()
        
        if today_chat:
            messages = self.db.query(MessageModel).filter(
                MessageModel.chat_uuid == today_chat.uuid
            ).order_by(MessageModel.created_at).all()
            return today_chat, messages, False
        else:
            # Create new chat for today
            new_chat, initial_question = self.create_chat(patient_uuid, commit=True)  # Commit the chat first
            
            # Create the first assistant message
            first_message = MessageModel(
                chat_uuid=new_chat.uuid,
                sender="assistant",
                message_type=initial_question["type"],
                content=initial_question["text"],
                structured_data={"options": initial_question["options"]} if initial_question.get("options") else None
            )
            
            # Add the message to the database
            self.db.add(first_message)
            self.db.commit()
            self.db.refresh(first_message)
            
            return new_chat, [first_message], True

    def force_create_today_session(self, patient_uuid: UUID, user_timezone: str = "America/Los_Angeles") -> Tuple[ChatModel, List[MessageModel], bool]:
        """
        Forces the creation of a new chat session for today, bypassing any existing sessions.
        Uses user's timezone to determine what "today" means.
        """
        new_chat, initial_question = self.create_chat(patient_uuid, commit=True)  # Commit the chat first
        
        # Create the first assistant message
        first_message = MessageModel(
            chat_uuid=new_chat.uuid,
            sender="assistant",
            message_type=initial_question["type"],
            content=initial_question["text"],
            structured_data={"options": initial_question["options"]} if initial_question.get("options") else None
        )
        
        # Add the message to the database
        self.db.add(first_message)
        self.db.commit()
        self.db.refresh(first_message)
        
        return new_chat, [first_message], True

    async def process_message(self, chat_uuid: UUID, message: WebSocketMessageIn) -> ProcessResponse:
        """Processes a message, updating state and replying in a single transaction."""
        chat = self.db.query(ChatModel).filter(ChatModel.uuid == chat_uuid).first()
        if not chat:
            # This should ideally not happen if client gets UUID from backend
            raise ValueError("Chat not found.")

        # 1. Create the user message object and save it
        user_msg = MessageModel(
            chat_uuid=chat_uuid,
            sender="user",
            message_type="button_response",
            content=message.content,
            structured_data=message.structured_data
        )
        self.db.add(user_msg)
        self.db.flush() # Ensure the user message gets an ID before the assistant replies

        # 2. Determine next state and assistant response details
        new_state, assistant_response_details = self._determine_next_state_and_response(chat, message)
        
        # 3. Create the assistant message object
        assistant_msg = MessageModel(
             chat_uuid=chat_uuid,
             sender="assistant",
             message_type=assistant_response_details.message_type,
             content=assistant_response_details.content,
             structured_data={"options": assistant_response_details.options} if assistant_response_details.options else None
        )
        
        # 4. Add all new objects to the session and commit once
        self.db.add_all([chat, assistant_msg])
        self.db.commit()
        
        # 5. Prepare the full response payload
        return ProcessResponse(
            user_message_saved=Message.from_orm(user_msg),
            assistant_response=Message.from_orm(assistant_msg),
            conversation_updated=ConversationUpdate(new_state=new_state, symptom_list=chat.symptom_list)
        )

    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """Safely extracts a JSON object from a string that might contain other text."""
        try:
            # Find the start of the JSON object
            json_start = text.find('{')
            if json_start == -1:
                return None
            
            json_end = text.rfind('}') + 1
            if json_end == 0:
                return None

            json_str = text[json_start:json_end]
            parsed_json = json.loads(json_str)

            # Standardize response_type to use underscores
            if 'response_type' in parsed_json and isinstance(parsed_json['response_type'], str):
                parsed_json['response_type'] = parsed_json['response_type'].replace('-', '_')
            
            return parsed_json
        except (json.JSONDecodeError, IndexError):
            return None

    async def process_message_stream(self, chat_uuid: UUID, message: WebSocketMessageIn) -> AsyncGenerator[Any, None]:
        """
        Processes a message, gets a structured JSON response from the LLM,
        and yields the appropriate message objects to the client.
        """
        chat = self.db.query(ChatModel).filter(ChatModel.uuid == chat_uuid).first()
        if not chat:
            return

        # 1. Save and yield the user's message
        user_msg = MessageModel(
            chat_uuid=chat_uuid,
            sender="user",
            message_type=message.message_type,
            content=message.content,
        )
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)
        yield Message.from_orm(user_msg)

        # 2. Get the full conversation history to send to the LLM
        chat_history = self.db.query(MessageModel).filter(MessageModel.chat_uuid == chat.uuid).order_by(MessageModel.id.asc()).all()
        history_for_llm = [Message.from_orm(m).model_dump(mode='json') for m in chat_history]
        
        context = {
            "latest_input": message.content,
            "history": history_for_llm
        }

        # 3. Stream the LLM response and build the full JSON string
        llm_response_generator = self._query_knowledge_base_stream(context)
        full_response_text = ""
        for chunk_content in llm_response_generator:
            full_response_text += chunk_content
        
        # 4. Parse the complete JSON response
        llm_json = self._extract_json_from_response(full_response_text)

        if not llm_json:
            print(f"ERROR: Could not parse JSON from LLM response: {full_response_text}")
            # Yield a fallback error message
            yield WebSocketMessageChunk(message_id=-1, content="I'm sorry, I encountered an error. Please try again.")
            yield WebSocketStreamEnd(message_id=-1)
            return
            
        # 5. Process the structured response
        response_type = llm_json.get("response_type", "text")
        content = llm_json.get("content", "I'm not sure how to respond.")
        options = llm_json.get("options")
        new_symptoms = llm_json.get("new_symptoms", [])

        # Update chat with any newly identified symptoms
        if new_symptoms:
            chat.symptom_list = list(set((chat.symptom_list or []) + new_symptoms))
            self.db.commit()

        # If the user is responding with their feeling, save it to the chat
        if message.message_type == 'feeling_response':
            chat.overall_feeling = message.content
            self.db.commit()

        # Normalize message type for database storage (convert hyphenated to underscore)
        db_message_type = response_type.replace('-', '_')
        if response_type.lower() in ["summary", "end"]:
            db_message_type = 'text'

        # 6. Save and yield the assistant's message
        # If this is the summary, format the content for the user
        if response_type == "summary":
            summary_data = llm_json.get("summary_data", {})
            bulleted_summary = summary_data.get("bulleted_summary", "No summary available.")
            
            # Format the bulleted summary with proper bullet points
            if bulleted_summary and bulleted_summary != "No summary available.":
                # Handle both string and list formats
                if isinstance(bulleted_summary, list):
                    # If it's already a list, use it directly
                    bullet_lines = bulleted_summary
                else:
                    # If it's a string, split by newlines
                    bullet_lines = bulleted_summary.split('\n')
                
                formatted_bullets = []
                for line in bullet_lines:
                    if isinstance(line, str) and line.strip():  # Only add non-empty string lines
                        formatted_bullets.append(f"• {line.strip()}")
                    elif not isinstance(line, str) and line:  # Handle non-string items
                        formatted_bullets.append(f"• {str(line).strip()}")
                
                bullet_text = '<br>'.join(formatted_bullets) if formatted_bullets else "• No summary available."
            else:
                bullet_text = "• No summary available."
            
            content = f"<b>Thank you for completing this chat!</b><br><br>Here is your conversation summary:<br><br>{bullet_text}"

        assistant_msg = MessageModel(
            chat_uuid=chat_uuid,
            sender="assistant",
            message_type=db_message_type,
            content=content,
            structured_data={"options": options} if options else None
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)
        
        # Create the frontend message with the original response type
        frontend_message = Message.from_orm(assistant_msg)
        frontend_message.message_type = response_type if response_type != 'summary' else 'text'
        
        yield frontend_message

        # 7. If the conversation is done, update the chat with the summary and mark as completed
        if response_type in ["summary", "end"]:
            summary_data = llm_json.get("summary_data", {})
            
            chat.symptom_list = summary_data.get("symptom_list", chat.symptom_list)
            chat.severity_list = summary_data.get("severity_list", chat.severity_list)
            chat.longer_summary = summary_data.get("longer_summary", chat.longer_summary)
            chat.medication_list = summary_data.get("medication_list", chat.medication_list)
            chat.bulleted_summary = summary_data.get("bulleted_summary", chat.bulleted_summary)
            chat.overall_feeling = summary_data.get("overall_feeling", chat.overall_feeling)

            if response_type == "summary":
                chat.conversation_state = ConversationState.COMPLETED
            elif response_type == "end":
                chat.conversation_state = ConversationState.EMERGENCY

            self.db.commit()

    def get_connection_ack(self, chat_uuid: UUID) -> ConnectionEstablished:
        """Acknowledges a WebSocket connection with the current chat state."""
        # This message is for backend confirmation, not for display in the UI.
        # It can be logged on the client if needed.
        chat = self.db.query(ChatModel).filter(ChatModel.uuid == chat_uuid).first()
        if not chat:
            return None

        return ConnectionEstablished(
            content="Connection acknowledged.",
            chat_state={
                "conversation_state": chat.conversation_state
            }
        )
        
    def _query_knowledge_base(self, context: Dict[str, Any]) -> str:
        """
        Queries the configured LLM model with the provided context and document knowledge base.
        """
        print(f"KB_REAL: Querying {LLM_PROVIDER.upper()} with real context...")
        
        # 1. Load the knowledge base context from files
        model_inputs_path = os.path.join(os.path.dirname(__file__), '..', '..', 'model_inputs')
        context_loader = ContextLoader(model_inputs_path)
        
        system_prompt = context_loader.load_system_prompt()
        
        # Get patient symptoms from the context, default to an empty list
        patient_symptoms = context.get('patient_state', {}).get('current_symptoms', [])
        knowledge_base_context = context_loader.load_context(symptoms=patient_symptoms)

        # 2. Construct the user prompt for the LLM
        # We combine the general knowledge base with the specific conversation context
        user_prompt_parts = [
            "### Knowledge Base Context ###",
            knowledge_base_context,
            "\n### Conversation Context ###",
            f"Current Symptoms: {context.get('patient_state', {}).get('current_symptoms', [])}",
            f"Chat History (most recent messages): {json.dumps(context.get('history', []), indent=2)}",
            f"\n### User's Latest Message ###",
            f"User: \"{context.get('latest_input', '')}\"",
            "\n### Instructions ###",
            "Follow the conversation workflow defined in your system instructions. Remember to respond with valid JSON only."
        ]
        user_prompt = "\n".join(user_prompt_parts)

        # 3. Call the LLM provider
        llm_provider = get_llm_provider()
        response_generator = llm_provider.query(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # 4. Consume the streaming generator to get a single string response
        full_response = "".join([chunk for chunk in response_generator])
        
        print(f"KB_REAL: Received response from {LLM_PROVIDER.upper()}: '{full_response}'")
        return full_response if full_response else "I'm not sure what to ask next. Can you tell me more?"

    def _query_knowledge_base_stream(self, context: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Queries the configured LLM model with the provided context and document knowledge base.
        Yields chunks of the response as they become available.
        """
        print(f"KB_REAL: Streaming {LLM_PROVIDER.upper()} with real context...")
        
        # 1. Load the knowledge base context from files
        model_inputs_path = os.path.join(os.path.dirname(__file__), '..', '..', 'model_inputs')
        context_loader = ContextLoader(model_inputs_path)
        
        system_prompt = context_loader.load_system_prompt()
        
        # Get patient symptoms from the context, default to an empty list
        patient_symptoms = context.get('patient_state', {}).get('current_symptoms', [])
        knowledge_base_context = context_loader.load_context(symptoms=patient_symptoms)

        # 2. Construct the user prompt for the LLM
        # We combine the general knowledge base with the specific conversation context
        user_prompt_parts = [
            "### Knowledge Base Context ###",
            knowledge_base_context,
            "\n### Conversation Context ###",
            f"Current Symptoms: {context.get('patient_state', {}).get('current_symptoms', [])}",
            f"Chat History (most recent messages): {json.dumps(context.get('history', []), indent=2)}",
            f"\n### User's Latest Message ###",
            f"User: \"{context.get('latest_input', '')}\"",
            "\n### Instructions ###",
            "Follow the conversation workflow defined in your system instructions. Remember to respond with valid JSON only."
        ]
        user_prompt = "\n".join(user_prompt_parts)

        # 3. Call the LLM provider
        llm_provider = get_llm_provider()
        response_generator = llm_provider.query(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # 4. Yield chunks directly from the generator
        for chunk in response_generator:
            yield chunk
