# Deploying the OncoLife Chatbot

## Option 1: Railway (Recommended - Easiest)

### Step 1: Prepare Your Repository
```bash
# Make sure you're in the chatbot-standalone directory
cd chatbot-standalone

# Initialize git if not already done
git init
git add .
git commit -m "Initial chatbot commit"
```

### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your chatbot repository
5. Railway will automatically detect it's a Python app

### Step 3: Set Environment Variables
In Railway dashboard, go to your project → Variables tab and add:
```
LLM_PROVIDER=gpt4o
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 4: Get Your URL
Railway will give you a URL like: `https://your-app-name.railway.app`

---

## Option 2: Render (Alternative)

### Step 1: Create render.yaml
```yaml
services:
  - type: web
    name: oncolife-chatbot
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && python main.py
    envVars:
      - key: LLM_PROVIDER
        value: gpt4o
      - key: OPENAI_API_KEY
        sync: false
```

### Step 2: Deploy
1. Go to [render.com](https://render.com)
2. Connect your GitHub repo
3. Create new Web Service
4. Add your API keys in environment variables

---

## Option 3: Heroku (Legacy)

### Step 1: Install Heroku CLI
```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # macOS
```

### Step 2: Deploy
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-chatbot-name

# Set environment variables
heroku config:set LLM_PROVIDER=gpt4o
heroku config:set OPENAI_API_KEY=your_api_key

# Deploy
git push heroku main
```

---

## Frontend Deployment

### Option A: Vercel (Recommended)
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repo
3. Set build settings:
   - Framework Preset: Vite
   - Build Command: `cd frontend && npm run build`
   - Output Directory: `frontend/dist`
4. Add environment variable:
   - `VITE_API_URL=https://your-backend-url.com`

### Option B: Netlify
1. Go to [netlify.com](https://netlify.com)
2. Drag and drop your `frontend/dist` folder
3. Or connect GitHub repo

---

## Environment Variables Needed

### Backend (.env file or platform variables):
```
LLM_PROVIDER=gpt4o  # or groq, cerebras
OPENAI_API_KEY=sk-...
GROQ_API_KEY=your_groq_key  # if using Groq
CEREBRAS_API_KEY=your_cerebras_key  # if using Cerebras
```

### Frontend (.env file):
```
VITE_API_URL=https://your-backend-url.com
```

---

## Testing Your Deployment

1. **Backend Test**: Visit `https://your-backend-url.com/`
   - Should show: `{"message": "OncoLife Chatbot API is running"}`

2. **Frontend Test**: Visit your frontend URL
   - Should load the chatbot interface
   - Try sending a message to test WebSocket connection

---

## Troubleshooting

### Common Issues:
1. **Build Fails**: Check Python version (3.11+ required)
2. **API Errors**: Verify environment variables are set
3. **WebSocket Issues**: Check if platform supports WebSockets
4. **CORS Errors**: Backend CORS is configured for localhost:3000

### Debug Commands:
```bash
# Check logs
railway logs  # or heroku logs --tail

# Test locally first
cd backend && python main.py
cd frontend && npm run dev
```

---

## Cost Estimates

- **Railway**: $5-20/month (depending on usage)
- **Render**: $7-25/month
- **Heroku**: $7-25/month
- **Vercel**: Free tier available
- **Netlify**: Free tier available

**Total**: ~$10-30/month for full deployment 