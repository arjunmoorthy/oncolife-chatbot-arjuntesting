from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.chat.simple_chat_routes import router as chat_router
from startup_optimizer import preload_everything

# Pre-load models and data at startup
print("🚀 Starting OncoLife Chatbot with optimization...")
context_loader = preload_everything()

app = FastAPI(title="OncoLife Chatbot API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include chat routes
app.include_router(chat_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "OncoLife Chatbot API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 