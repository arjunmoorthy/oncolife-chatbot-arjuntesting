import uuid
from typing import Dict, Any, Tuple
from constants import ConversationState
from llm.gpt import GPT4oProvider
from llm.context import ContextLoader
from models import WebSocketMessageIn, WebSocketMessageOut
from datetime import datetime
import json
import os

class TestChatLogic:
    """Exact same conversation logic as patient-portal/develop, but without database dependencies."""
    
    def __init__(self):
        self.conversations = {}  # In-memory conversation storage
        self.llm_provider = GPT4oProvider()
        self.context_loader = ContextLoader("model_inputs")
    
    def _get_or_create_conversation(self, chat_uuid: str) -> Dict[str, Any]:
        """Get existing conversation or create a new one."""
        if chat_uuid not in self.conversations:
            self.conversations[chat_uuid] = {
                'state': ConversationState.CHEMO_CHECK_SENT,
                'messages': [],
                'symptom_list': []
            }
        return self.conversations[chat_uuid]
    
    def _determine_next_state_and_response(self, conversation: Dict[str, Any], message: str) -> Tuple[str, str, str, list]:
        """The EXACT same state machine as patient-portal/develop."""
        current_state = conversation['state']
        next_state = current_state
        response_content = "I'm not sure how to respond to that. Can you try again?"
        response_options = []
        response_type = "text"

        if current_state == ConversationState.COMPLETED:
            response_content = "This conversation has ended. Please start a new one if you need assistance."
        
        elif current_state == ConversationState.CHEMO_CHECK_SENT:
            # EXACT same logic as patient-portal
            next_state = ConversationState.SYMPTOM_SELECTION_SENT
            response_content = "Thank you. What symptoms are you experiencing? You can select multiple."
            response_type = "multi_select"
            response_options = [
                "Fever", "Nausea", "Vomiting", "Diarrhea", "Constipation", "Fatigue",
                "Headache", "Mouth Sores", "Rash", "Shortness of Breath", "Other"
            ]

        elif current_state == ConversationState.SYMPTOM_SELECTION_SENT:
            # EXACT same logic as patient-portal
            next_state = ConversationState.FOLLOWUP_QUESTIONS
            symptoms = [s.strip() for s in message.split(',')]
            current_symptoms = conversation['symptom_list'] or []
            conversation['symptom_list'] = list(set(current_symptoms + symptoms))
            
            context = {"patient_state": {"current_symptoms": conversation['symptom_list']}}
            response_content = self._query_knowledge_base(context)

        elif current_state == ConversationState.FOLLOWUP_QUESTIONS:
            # EXACT same logic as patient-portal
            # Get conversation history (last 20 messages)
            recent_messages = conversation['messages'][-20:] if len(conversation['messages']) > 20 else conversation['messages']
            history_for_llm = [{"sender": msg['sender'], "content": msg['content']} for msg in recent_messages]
            
            context = {
                "patient_state": {"current_symptoms": conversation['symptom_list']},
                "latest_input": message,
                "history": history_for_llm
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
        
        # Update conversation state
        conversation['state'] = next_state
        
        return next_state, response_content, response_type, response_options
    
    def _query_knowledge_base(self, context: Dict[str, Any]) -> str:
        """EXACT same RAG logic as patient-portal/develop."""
        print(f"KB_REAL: Querying GPT4o with real context...")
        
        # 1. Load the knowledge base context from files
        system_prompt = self.context_loader.load_system_prompt()
        
        # Get patient symptoms from the context, default to an empty list
        patient_symptoms = context.get('patient_state', {}).get('current_symptoms', [])
        knowledge_base_context = self.context_loader.load_context(symptoms=patient_symptoms)

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
        response_generator = self.llm_provider.query(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # 4. Consume the streaming generator to get a single string response
        full_response = "".join([chunk for chunk in response_generator])
        
        print(f"KB_REAL: Received response from GPT4o: '{full_response}'")
        return full_response if full_response else "I'm not sure what to ask next. Can you tell me more?"
    
    def generate_reply(self, user_message: str, chat_uuid: str = "test-chat") -> Dict[str, Any]:
        """Generate a reply using the EXACT same logic as patient-portal/develop."""
        # Get or create conversation
        conversation = self._get_or_create_conversation(chat_uuid)
        
        # Add user message to history
        conversation['messages'].append({
            'sender': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Determine next state and response using EXACT same logic
        next_state, response_content, response_type, response_options = self._determine_next_state_and_response(conversation, user_message)
        
        # Add assistant response to history
        conversation['messages'].append({
            'sender': 'assistant',
            'content': response_content,
            'message_type': response_type,
            'options': response_options,
            'timestamp': datetime.now().isoformat()
        })
        
        # Return simple response format
        return {
            'message': response_content,
            'sender': 'bot',
            'message_type': response_type,
            'options': response_options,
            'state': next_state
        } 