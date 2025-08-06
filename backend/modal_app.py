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

@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def chat_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main chat endpoint that handles user messages and returns AI responses.
    Uses the existing chatbot services with full LLM and RAG functionality.
    """
    try:
        # Debug: Add current directory to Python path
        import os, sys
        sys.path.insert(0, os.getcwd())  # ensure current working dir is searched first
        
        # Import here to avoid issues with Modal's container
        from routers.chat.services import ConversationService
        from routers.chat.models import ChatMessage
        from startup_optimizer import preload_everything
        
        # Get user message from payload
        user_message = payload.get("message", "")
        chat_uuid = payload.get("chat_uuid", "default-chat")
        
        if not user_message:
            return {"error": "No message provided"}
        
        # Initialize conversation service (this will load models on first call)
        conversation_service = ConversationService()
        
        # Create chat message
        chat_message = ChatMessage(
            content=user_message,
            role="user",
            chat_uuid=chat_uuid
        )
        
        # Process the message through the existing chatbot logic
        response = conversation_service.process_message(chat_message)
        
        # Return the AI response
        return {
            "reply": response.content,
            "chat_uuid": chat_uuid,
            "timestamp": response.timestamp.isoformat() if response.timestamp else None
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
    This can be called once before starting to use the chatbot.
    """
    try:
        # Debug: Add current directory to Python path
        import os, sys
        sys.path.insert(0, os.getcwd())  # ensure current working dir is searched first
        
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