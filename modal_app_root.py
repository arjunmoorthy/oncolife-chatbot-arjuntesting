import modal
import os
import sys
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, "/app")

# Create Modal app
app = modal.App("oncolife-chatbot")

# Create the base image with all dependencies
image = modal.Image.debian_slim().pip_install(
    "fastapi",
    "uvicorn",
    "openai",
    "pydantic",
    "sqlalchemy",
    "python-docx",
    "sentence-transformers",
    "faiss-cpu",
    "numpy",
    "pandas",
    "groq",
    "cerebras-cloud-sdk",
    "pypdf"
).add_local_dir(".", "/app")

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("openai-secret")],
    timeout=300
)
@modal.fastapi_endpoint(method="POST")
def test_chat_endpoint(payload: dict):
    """Clean test endpoint without database dependencies."""
    try:
        import sys
        sys.path.insert(0, "/app")
        from test_chat_logic import TestChatLogic
        
        # Get user message from payload
        user_message = payload.get("message", "")
        chat_uuid = payload.get("chat_uuid", "test-chat")
        
        if not user_message:
            return {"error": "No message provided"}
        
        # Initialize the test chat logic
        chat_logic = TestChatLogic()
        
        # Generate reply using pure logic
        response = chat_logic.generate_reply(user_message, chat_uuid)
        
        # Return simple response format
        return {
            "message": response['message'],
            "sender": response['sender'],
            "message_type": response['message_type'],
            "options": response['options'],
            "state": response['state'],
            "chat_uuid": chat_uuid
        }
        
    except Exception as e:
        return {"error": f"Error processing message: {str(e)}"}

@app.function(
    image=image,
    timeout=60
)
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("openai-secret")],
    timeout=300
)
def initialize_models():
    """Initialize models and context loaders."""
    try:
        import sys
        sys.path.insert(0, "/app")
        from llm.context import ContextLoader
        
        # Initialize context loader
        context_loader = ContextLoader("model_inputs")
        
        return {"status": "Models initialized successfully"}
        
    except Exception as e:
        return {"error": f"Error initializing models: {str(e)}"}

@app.local_entrypoint()
def main():
    """Local entrypoint for testing."""
    print("OncoLife Chatbot is running!")
    print("Test the endpoints:")
    print("1. Health check: curl -X POST https://arjunmoorthy--oncolife-chatbot-health-check-dev.modal.run")
    print("2. Test endpoint: curl -X POST https://arjunmoorthy--oncolife-chatbot-test-chat-endpoint-dev.modal.run -H 'Content-Type: application/json' -d '{\"message\":\"hello\"}'") 