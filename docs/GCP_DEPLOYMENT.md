# GCP Cloud Run Deployment Guide

## Overview
Deploy the AIOps Platform to Google Cloud Platform using Cloud Run (free tier).

**What we'll deploy:**
- Backend (FastAPI) → Cloud Run
- Frontend (React) → Cloud Run
- PostgreSQL → Supabase (free)
- Redis → Upstash (free)
- Qdrant → Qdrant Cloud (free)

**Estimated Cost: $0/month** (within free tier limits)

---

## Prerequisites

1. **Google Cloud Account** - https://cloud.google.com (free $300 credits)
2. **GitHub Account** - to store your code
3. **Supabase Account** - https://supabase.com (free PostgreSQL)
4. **Upstash Account** - https://upstash.com (free Redis)
5. **Qdrant Cloud Account** - https://cloud.qdrant.io (free vector DB)

---

## Step 1: Push Code to GitHub

```bash
cd "/Users/ashwingurumoorthy/Documents/Default Project/agentic-aiops-platform"

# Initialize git
git init
git add .
git commit -m "Initial commit - AIOps Platform"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/agentic-aiops-platform.git
git branch -M main
git push -u origin main
```

---

## Step 2: Set Up Free Databases

### 2a. Supabase (PostgreSQL)
1. Go to https://supabase.com and sign up
2. Click "New Project"
3. Set name: `aiops-db`, set a password
4. Wait for it to be created
5. Go to Settings → Database → Connection string → URI
6. Copy the URI and save it (looks like: `postgresql://postgres:password@db.xxx.supabase.co:5432/postgres`)

### 2b. Upstash (Redis)
1. Go to https://upstash.com and sign up
2. Click "Create Database"
3. Set name: `aiops-redis`, select region closest to you
4. Copy the "Redis URL" (looks like: `rediss://default:password@xxx.upstash.io:6379`)

### 2c. Qdrant Cloud (Vector DB)
1. Go to https://cloud.qdrant.io and sign up
2. Click "New Cluster"
3. Select free tier, name it `aiops`
4. Copy the cluster URL and API key

---

## Step 3: Deploy Backend to Cloud Run

### 3a. Install Google Cloud CLI
```bash
brew install --cask google-cloud-sdk
gcloud init  # Sign in with your Google account
```

### 3b. Enable required APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 3c. Build and deploy backend
```bash
cd "/Users/ashwingurumoorthy/Documents/Default Project/agentic-aiops-platform"

# Build the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aiops-backend -f Dockerfile.backend .

# Deploy to Cloud Run
gcloud run deploy aiops-backend \
  --image gcr.io/YOUR_PROJECT_ID/aiops-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars "APP_ENV=production,APP_DEBUG=false,CORS_ORIGINS=[\"https://YOUR_FRONTEND_URL\"]" \
  --set-secrets "APP_SECRET_KEY=APP_SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,ENCRYPTION_KEY=ENCRYPTION_KEY:latest,REDIS_URL=REDIS_URL:latest,QDRANT_URL=QDRANT_URL:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

Save the backend URL (looks like: `https://aiops-backend-xxxx-uc.a.run.app`)

---

## Step 4: Deploy Frontend to Cloud Run

### 4a. Update nginx.conf with backend URL
Edit `frontend/nginx.conf` and replace `BACKEND_URL` with your backend Cloud Run URL:
```nginx
proxy_pass https://aiops-backend-xxxx-uc.a.run.app;
```

### 4b. Build and deploy frontend
```bash
cd "/Users/ashwingurumoorthy/Documents/Default Project/agentic-aiops-platform"

# Build the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aiops-frontend -f Dockerfile.frontend .

# Deploy to Cloud Run
gcloud run deploy aiops-frontend \
  --image gcr.io/YOUR_PROJECT_ID/aiops-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 256Mi \
  --min-instances 0 \
  --max-instances 2
```

Save the frontend URL (looks like: `https://aiops-frontend-xxxx-uc.a.run.app`)

---

## Step 5: Update CORS

Update the backend CORS to allow your frontend URL:
```bash
gcloud run services update aiops-backend \
  --update-env-vars "CORS_ORIGINS=[\"https://YOUR_FRONTEND_URL\"]"
```

---

## Step 6: Test Your Deployment

Open your frontend URL in a browser:
```
https://aiops-frontend-xxxx-uc.a.run.app
```

Check backend health:
```
https://aiops-backend-xxxx-uc.a.run.app/api/v1/health
```

Check API docs:
```
https://aiops-backend-xxxx-uc.a.run.app/docs
```

---

## Quick Commands Reference

```bash
# View logs
gcloud run services logs read aiops-backend --region us-central1

# Update backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aiops-backend -f Dockerfile.backend .
gcloud run deploy aiops-backend --image gcr.io/YOUR_PROJECT_ID/aiops-backend --region us-central1

# Update frontend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/aiops-frontend -f Dockerfile.frontend .
gcloud run deploy aiops-frontend --image gcr.io/YOUR_PROJECT_ID/aiops-frontend --region us-central1

# Delete services (to stop billing)
gcloud run services delete aiops-backend --region us-central1
gcloud run services delete aiops-frontend --region us-central1
```

---

## Free Tier Limits

| Service | Free Limit |
|---------|-----------|
| Cloud Run | 240,000 vCPU-seconds/month |
| Supabase | 500MB database, 50K monthly active users |
| Upstash | 10,000 commands/day |
| Qdrant Cloud | 1GB storage, 1M vectors |

**For a demo/portfolio project, this is more than enough.**
