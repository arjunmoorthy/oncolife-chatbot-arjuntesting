#!/bin/bash

echo "🚀 OncoLife Chatbot Deployment Script"
echo "======================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial chatbot commit"
fi

echo "✅ Repository ready for deployment"
echo ""
echo "🌐 Deployment Options:"
echo "1. Railway (Recommended) - railway.app"
echo "2. Render - render.com"
echo "3. Heroku - heroku.com"
echo ""
echo "📋 Next Steps:"
echo "1. Push to GitHub: git remote add origin YOUR_GITHUB_REPO_URL"
echo "2. Deploy backend to your chosen platform"
echo "3. Deploy frontend to Vercel/Netlify"
echo "4. Set environment variables (see DEPLOYMENT.md)"
echo ""
echo "🔑 Required Environment Variables:"
echo "- LLM_PROVIDER=gpt4o"
echo "- OPENAI_API_KEY=your_api_key"
echo "- VITE_API_URL=https://your-backend-url.com"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions" 