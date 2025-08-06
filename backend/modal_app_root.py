import modal
from typing import Dict, Any
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Modal app
app = modal.App("oncolife-chatbot")

# Define the container image with all dependencies
image = (
    modal.Image.debian_slim()
    .pip_install([
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "websockets==12.0",
        "python-multipart==0.0.6",
        "boto3",
        "python-dotenv",
        "python-jose[cryptography]",
        "email_validator",
        "requests",
        "groq",
        "cerebras-cloud-sdk",
        "openai",
        "python-docx",
        "pypdf",
        "numpy",
        "pytz",
        "sentence_transformers",
        "faiss-cpu"
    ])
)

@app.function(image=image, secrets=[modal.Secret.from_name("openai-secret")])
@modal.fastapi_endpoint(method="POST")
def chat_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    OncoLife chat endpoint using the real conversation system with RAG.
    """
    try:
        from startup_optimizer import get_context_loader
        from llm.gpt import GPT4oProvider
        from llm.groq import GroqProvider
        from llm.cerebras import CerebrasProvider
        from services import ConversationService
        
        # Get user message from payload
        user_message = payload.get("message", "")
        chat_uuid = payload.get("chat_uuid", "default-chat")
        
        if not user_message:
            return {"error": "No message provided"}
        
        # Initialize the context loader (RAG system)
        context_loader = get_context_loader()
        
        # Get LLM provider
        llm_provider = GPT4oProvider()
        
        # Create a mock database session for the conversation service
        class MockDB:
            def commit(self): pass
            def refresh(self, obj): pass
            def add(self, obj): pass
            def query(self, model): return MockQuery()
        
        class MockQuery:
            def filter(self, *args): return self
            def first(self): return None
            def all(self): return []
            def order_by(self, *args): return self
            def limit(self, num): return self
        
        # Initialize conversation service
        conversation_service = ConversationService(MockDB())
        
        # Get context for the user's message
        context = context_loader.load_context() if context_loader else ""
        
        # Create a simple chat message
        from modal_models import ChatMessage
        chat_message = ChatMessage(
            content=user_message,
            role="user",
            chat_uuid=chat_uuid
        )
        
        # Process through the conversation service
        response = conversation_service.process_message(chat_message)
        
        # Return the AI response
        return {
            "reply": response.content,
            "chat_uuid": chat_uuid,
            "timestamp": response.timestamp.isoformat() if response.timestamp else "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        return {"error": f"Error processing message: {str(e)}"}

@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def health_check() -> Dict[str, str]:
    """Health check endpoint to verify the service is running."""
    return {"status": "healthy", "message": "OncoLife Chatbot is running"}

@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def initialize_models() -> Dict[str, str]:
    """
    Endpoint to pre-load models and initialize the RAG system.
    """
    try:
        from startup_optimizer import preload_everything
        
        # Pre-load everything (FAISS, embeddings, etc.)
        context_loader = preload_everything()
        
        return {
            "status": "success",
            "message": "Models initialized successfully",
            "models_loaded": "FAISS, Sentence Transformers, and LLM providers"
        }
        
    except Exception as e:
        return {"error": f"Failed to initialize models: {str(e)}"} 