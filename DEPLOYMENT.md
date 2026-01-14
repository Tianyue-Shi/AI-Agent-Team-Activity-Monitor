# Deployment Guide - Railway

This guide walks you through deploying the Team Activity Monitor to Railway.

## Prerequisites

1. A [Railway account](https://railway.app) (sign up with GitHub for easiest setup)
2. Your code pushed to a GitHub repository
3. API keys ready:
   - OpenAI API key (or Anthropic/Claude key)
   - GitHub Personal Access Token (optional, for real GitHub data)
   - JIRA credentials (optional, for real JIRA data)

---

## Architecture Overview

Railway will run **two services**:

```
┌─────────────────────────────────────────────────────────┐
│                      Railway Project                     │
├─────────────────────────┬───────────────────────────────┤
│     Backend Service     │     Frontend Service          │
│     (Python/FastAPI)    │     (React/Vite)              │
│                         │                               │
│  api.your-app.up.railway.app   your-app.up.railway.app  │
└─────────────────────────┴───────────────────────────────┘
```

---

## Step-by-Step Deployment

### Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your `AI-Agent-Team-Activity-Monitor` repository

### Step 2: Deploy Backend Service

1. After connecting the repo, Railway creates a service
2. Click on the service → **Settings**
3. Set **Root Directory** to: `backend`
4. Railway will auto-detect Python and deploy

#### Add Backend Environment Variables

Go to **Variables** tab and add:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Claude API key (alternative to OpenAI) |
| `GITHUB_TOKEN` | No | GitHub Personal Access Token for real data |
| `JIRA_BASE_URL` | No | e.g., `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | No | Your JIRA account email |
| `JIRA_API_TOKEN` | No | JIRA API token |
| `CORS_ORIGINS` | Yes | Will be set after frontend deploys |
| `DEBUG` | No | Set to `false` for production |

*At least one AI provider key is required

5. Click **Deploy** or it will auto-deploy
6. Once deployed, note the backend URL (e.g., `your-backend.up.railway.app`)

### Step 3: Deploy Frontend Service

1. In the same Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select the same repository again
3. Click on the new service → **Settings**
4. Set **Root Directory** to: `frontend`
5. Set **Build Command** to: `npm install && npm run build`
6. Set **Start Command** to: `npx serve -s dist -l $PORT`

#### Add Frontend Environment Variable

Go to **Variables** tab and add:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-backend.up.railway.app` (your backend URL from Step 2) |

**Important:** The `VITE_` prefix is required for Vite to expose it to the frontend.

### Step 4: Update Backend CORS

Now that frontend is deployed, go back to your **backend service**:

1. Go to **Variables** tab
2. Add or update `CORS_ORIGINS`:
   ```
   https://your-frontend.up.railway.app,http://localhost:5173
   ```
   (Replace with your actual frontend URL)

### Step 5: Verify Deployment

1. Visit your frontend URL
2. The chat interface should load
3. Try asking: "What is John working on?"
4. Check the backend health: `https://your-backend.up.railway.app/health`

---

## Environment Variables Reference

### Backend (`/backend`)

```bash
# AI Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# External Integrations (optional - uses mock data if not set)
GITHUB_TOKEN=ghp_...
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=...

# CORS (required - comma-separated origins)
CORS_ORIGINS=https://your-frontend.up.railway.app,http://localhost:5173

# Database (Railway provides this, or uses SQLite)
DATABASE_URL=sqlite+aiosqlite:///./team_monitor.db

# Debug mode
DEBUG=false
```

### Frontend (`/frontend`)

```bash
# Backend API URL (required)
VITE_API_URL=https://your-backend.up.railway.app
```

---

## Custom Domain (Optional)

1. In Railway, click on your service → **Settings** → **Domains**
2. Click **"+ Custom Domain"**
3. Add your domain (e.g., `api.yourdomain.com` for backend)
4. Update DNS records as instructed
5. Update `CORS_ORIGINS` if you add a custom domain to frontend

---

## Troubleshooting

### Frontend can't connect to backend

1. Check browser console for CORS errors
2. Verify `CORS_ORIGINS` includes your frontend URL (with `https://`)
3. Verify `VITE_API_URL` is set correctly (with `https://`)
4. Redeploy frontend after changing `VITE_API_URL`

### AI responses not working

1. Check backend logs in Railway dashboard
2. Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
3. Test directly: `https://your-backend.up.railway.app/debug/ai-status`

### Mock data instead of real data

This is expected if you haven't configured:
- `GITHUB_TOKEN` for real GitHub data
- `JIRA_*` variables for real JIRA data

The app works with mock data for demos!

---

## Costs

Railway pricing (as of 2024):
- **Hobby Plan**: $5/month credit (usually enough for small projects)
- **Pay-as-you-go**: ~$0.000231/minute for compute

Your app will likely cost **$0-5/month** depending on usage.

---

## Continuous Deployment

Railway automatically redeploys when you push to your main branch:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Railway auto-deploys! 🚀
```

---

## Local Development After Setup

Your local development still works the same way:

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # or your virtual env
uvicorn app.main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

The frontend will use `http://localhost:8000` locally (the default in `client.js`).
