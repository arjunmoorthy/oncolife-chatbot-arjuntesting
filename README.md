# OncoLife Chatbot Standalone

A standalone version of the OncoLife chatbot with full LLM and RAG functionality. This version removes database dependencies and authentication but keeps all the intelligent conversation logic.

## Features

- Real-time WebSocket communication
- Multi-select and single-select interactions
- Feeling selection
- Medical symptom assessment workflow
- Responsive chat interface
- Full LLM integration (OpenAI, Groq, or Cerebras)
- RAG (Retrieval Augmented Generation) with medical knowledge base
- No authentication required for testing

## Project Structure

```
chatbot-standalone/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/chat/  # Chat UI components
│   │   ├── pages/           # Chat page
│   │   ├── services/        # API services
│   │   ├── hooks/           # WebSocket hook
│   │   └── types/           # TypeScript types
│   └── package.json
├── backend/                  # FastAPI Python backend
│   ├── routers/chat/        # Chat routes and services
│   ├── model_inputs/        # Chatbot instructions and data
│   ├── main.py              # FastAPI app
│   └── requirements.txt
└── README.md
```

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd chatbot-standalone/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env_example.txt .env
   # Edit .env and add your API keys
   ```

5. **Start the backend server:**
   ```bash
   python main.py
   ```
   
   The backend will run on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd chatbot-standalone/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The frontend will run on `http://localhost:3000`

## Usage

1. Open your browser and go to `http://localhost:3000`
2. The chatbot will automatically start a new session
3. Follow the conversation flow:
   - Answer whether you received chemotherapy
   - Select your symptoms (multiple selection allowed)
   - Rate severity for each symptom
   - Provide your overall feeling
   - Review the summary

## Key Differences from Original

### Simplified Backend
- **No Database**: Uses in-memory storage instead of SQLAlchemy
- **No Authentication**: Removed JWT token requirements
- **Full LLM Integration**: Uses real GPT/Groq/Cerebras APIs
- **Full RAG System**: Includes medical knowledge base and semantic search

### Simplified Frontend
- **No Auth**: Removed authentication token handling
- **No User Management**: Single chat session per page load
- **Simplified Services**: Direct API calls without auth headers

## Development

### Adding New Features

1. **Backend**: Modify `chat_services.py` to add new conversation logic
2. **Frontend**: Update `SimpleChatsPage.tsx` to handle new message types
3. **Components**: Add new UI components in `components/chat/`

### Testing

- Backend: The simplified version is perfect for testing the chat flow
- Frontend: Test different user interactions and message types
- Integration: Verify WebSocket communication works correctly

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure backend is running on port 8000
   - Check browser console for connection errors

2. **Frontend Not Loading**
   - Verify npm dependencies are installed
   - Check if port 3000 is available

3. **Backend Import Errors**
   - Ensure virtual environment is activated
   - Verify all requirements are installed

### Port Conflicts

If ports are in use, you can change them:
- Backend: Modify `main.py` line with `port=8000`
- Frontend: Modify `vite.config.ts` server port

## Next Steps

To integrate with the full system:
1. Add database models and SQLAlchemy
2. Implement JWT authentication
3. Integrate with actual LLM providers
4. Add user management and session persistence

## License

This is a development/testing version of the OncoLife chatbot system. 