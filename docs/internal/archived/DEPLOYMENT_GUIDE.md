# FE-EKG Deployment Guide

Complete guide for deploying the FE-EKG system to production using Railway (backend) and Vercel (frontend).

---

## Overview

FE-EKG consists of two separately deployed components:

1. **Backend (Flask API)** → Deploy to **Railway** (recommended) or Render/Fly.io
2. **Frontend (Next.js)** → Deploy to **Vercel** (one-click deploy)

**Deployment Time:** ~30 minutes for both components

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Production Architecture                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      HTTPS       ┌──────────────┐      SPARQL
│   Vercel     │─────────────────▶│   Railway    │──────────────▶
│  (Frontend)  │                  │  (Backend)   │
│              │                  │              │
│ Next.js 15   │                  │  Flask API   │
│ React Query  │                  │  Gunicorn    │
│ Cytoscape.js │                  │  Python 3.10 │
└──────────────┘                  └──────────────┘
                                         │
                                         │ SPARQL
                                         ▼
                                  ┌──────────────┐
                                  │ AllegroGraph │
                                  │  (Cloud DB)  │
                                  │              │
                                  │ qa-agraph    │
                                  │ .nelumbium   │
                                  │ .ai          │
                                  └──────────────┘

User → Vercel Frontend → Railway Backend → AllegroGraph
```

---

## Quick Deploy (5 Minutes)

### Prerequisites

- [ ] GitHub account
- [ ] Railway account (free tier OK)
- [ ] Vercel account (free tier OK)
- [ ] AllegroGraph credentials (already configured)
- [ ] Backend repository: This repo
- [ ] Frontend repository: https://github.com/JunjieAraoXiong/feekg-frontend

### Step 1: Deploy Backend to Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# From backend repository root
cd /Users/hansonxiong/Desktop/DDP/feekg
railway init
railway up
```

**Set environment variables in Railway dashboard:**
```
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_CATALOG=mycatalog
AG_REPO=FEEKG
```

**Note your backend URL:** `https://your-app.up.railway.app`

### Step 2: Deploy Frontend to Vercel

```bash
# Visit https://vercel.com/new
# Import: https://github.com/JunjieAraoXiong/feekg-frontend
# Set environment variable:
NEXT_PUBLIC_API_URL=https://your-app.up.railway.app

# Click Deploy!
```

**Note your frontend URL:** `https://your-app.vercel.app`

### Step 3: Update CORS

Update `api/app.py` in backend:

```python
CORS(app, origins=[
    "http://localhost:3000",  # Local dev
    "https://your-app.vercel.app",  # Production
])
```

Redeploy backend:
```bash
railway up
```

**Done!** Your FE-EKG system is live.

---

## Detailed Backend Deployment (Railway)

### Why Railway?

- ✅ Easy Python deployment
- ✅ Free tier available
- ✅ Automatic SSL certificates
- ✅ Environment variable management
- ✅ GitHub integration
- ✅ Built-in monitoring

### Step-by-Step

#### 1. Create Railway Project

```bash
# Install CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd /Users/hansonxiong/Desktop/DDP/feekg
railway init
# Select: Create new project
# Name: feekg-backend
```

#### 2. Configure Environment Variables

In Railway dashboard (https://railway.app):

1. Go to your project
2. Click "Variables" tab
3. Add the following:

```bash
# AllegroGraph Configuration
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_CATALOG=mycatalog
AG_REPO=FEEKG

# Python Configuration (optional)
PYTHONUNBUFFERED=1
```

#### 3. Create Railway Configuration

Create `railway.json` in project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn -w 4 -b 0.0.0.0:$PORT api.app:app",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 4. Deploy

```bash
# Deploy to Railway
railway up

# View logs
railway logs

# Get deployment URL
railway domain
```

#### 5. Test Deployment

```bash
# Test health endpoint
curl https://your-app.up.railway.app/health

# Expected response:
# {"status": "healthy", "service": "FE-EKG API", "version": "1.0.0"}

# Test API
curl https://your-app.up.railway.app/api/info
```

### Railway Dashboard Features

**Logs:** Real-time application logs
```
railway logs
```

**Metrics:** CPU, memory, network usage
- View in dashboard under "Metrics" tab

**Environment:** Manage environment variables
- Dashboard → Variables

**Deployments:** Rollback to previous versions
- Dashboard → Deployments → Click deployment → Rollback

---

## Detailed Frontend Deployment (Vercel)

### Why Vercel?

- ✅ Built for Next.js (created by Vercel)
- ✅ One-click deploy from GitHub
- ✅ Automatic SSL certificates
- ✅ Global CDN
- ✅ Preview deployments for PRs
- ✅ Free tier generous

### Step-by-Step

#### 1. Prepare Frontend Repository

Ensure your frontend repo has:
- `package.json` with dependencies
- `next.config.js` properly configured
- Environment variables documented

#### 2. Deploy to Vercel

**Option A: Web Interface (Recommended)**

1. Go to https://vercel.com/new
2. Click "Import Project"
3. Paste: `https://github.com/JunjieAraoXiong/feekg-frontend`
4. Click "Import"
5. Configure project:
   - Framework Preset: Next.js
   - Root Directory: `./` (default)
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

6. Add environment variables:
```
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_DEFAULT_PAGE_SIZE=100
NEXT_PUBLIC_MAX_NODES=1000
```

7. Click "Deploy"

**Option B: Vercel CLI**

```bash
# Install CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd /path/to/feekg-frontend
vercel --prod

# Follow prompts:
# - Link to existing project? No
# - Project name: feekg-frontend
# - Deploy? Yes
```

#### 3. Configure Environment Variables

In Vercel dashboard:

1. Go to your project
2. Settings → Environment Variables
3. Add:

```
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_DEFAULT_PAGE_SIZE=100
NEXT_PUBLIC_MAX_NODES=1000
```

4. Redeploy to apply changes

#### 4. Test Deployment

```bash
# Visit your Vercel URL
open https://your-app.vercel.app

# Test API connection
# - Should load knowledge graph
# - Check browser console for errors
```

---

## CORS Configuration

**Critical:** Backend must allow requests from frontend domain.

### Update Backend CORS

Edit `api/app.py`:

```python
from flask_cors import CORS

app = Flask(__name__)

# BEFORE (development only)
CORS(app)  # Allows all origins - NOT SECURE

# AFTER (production)
CORS(app, origins=[
    "http://localhost:3000",              # Local development
    "https://feekg-frontend.vercel.app",  # Production frontend
    "https://your-custom-domain.com",     # Custom domain (if any)
])
```

### Redeploy Backend

```bash
# Commit changes
git add api/app.py
git commit -m "Update CORS for production"
git push

# Railway will auto-deploy, or manually:
railway up
```

### Test CORS

```bash
# From browser console on your Vercel frontend
fetch('https://your-backend.up.railway.app/api/info')
  .then(r => r.json())
  .then(console.log)

# Should return data, not CORS error
```

---

## Custom Domains (Optional)

### Backend Custom Domain (Railway)

1. Go to Railway dashboard
2. Click your project → Settings
3. Under "Domains", click "Generate Domain"
4. Or add custom domain:
   - Enter your domain (e.g., `api.yourdomain.com`)
   - Add CNAME record in your DNS:
     ```
     CNAME api.yourdomain.com → your-app.up.railway.app
     ```
   - Wait for SSL certificate (automatic)

### Frontend Custom Domain (Vercel)

1. Go to Vercel dashboard
2. Project → Settings → Domains
3. Add domain (e.g., `feekg.yourdomain.com`)
4. Configure DNS:
   ```
   CNAME feekg.yourdomain.com → cname.vercel-dns.com
   ```
5. Verify and wait for SSL

---

## Environment Variables Reference

### Backend (Railway)

| Variable | Value | Required | Description |
|----------|-------|----------|-------------|
| `AG_URL` | `https://qa-agraph.nelumbium.ai/` | ✅ Yes | AllegroGraph URL |
| `AG_USER` | `sadmin` | ✅ Yes | AllegroGraph username |
| `AG_PASS` | `279H-Dt<>,YU` | ✅ Yes | AllegroGraph password |
| `AG_CATALOG` | `mycatalog` | ✅ Yes | AllegroGraph catalog |
| `AG_REPO` | `FEEKG` | ✅ Yes | AllegroGraph repository |
| `PYTHONUNBUFFERED` | `1` | ⭕ No | Unbuffered Python output |
| `PORT` | Auto-set by Railway | 🔄 Auto | HTTP port |

### Frontend (Vercel)

| Variable | Value | Required | Description |
|----------|-------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.up.railway.app` | ✅ Yes | Backend API URL |
| `NEXT_PUBLIC_DEFAULT_PAGE_SIZE` | `100` | ⭕ No | Default pagination size |
| `NEXT_PUBLIC_MAX_NODES` | `1000` | ⭕ No | Max graph nodes to render |

---

## Deployment Checklist

### Pre-Deployment

- [ ] Backend code tested locally
- [ ] Frontend code tested locally
- [ ] Environment variables documented
- [ ] CORS configured correctly
- [ ] AllegroGraph credentials valid
- [ ] Database has data loaded (4,000 events)

### Backend Deployment

- [ ] Railway account created
- [ ] Project initialized (`railway init`)
- [ ] Environment variables set
- [ ] `railway.json` configured
- [ ] Deployed (`railway up`)
- [ ] Health check passes (`/health`)
- [ ] API endpoints work (`/api/info`)
- [ ] Logs show no errors (`railway logs`)

### Frontend Deployment

- [ ] Vercel account created
- [ ] Repository connected
- [ ] Environment variables set
- [ ] Deployed successfully
- [ ] Frontend loads without errors
- [ ] API connection works
- [ ] Browser console shows no CORS errors

### Post-Deployment

- [ ] CORS updated in backend
- [ ] Backend redeployed with CORS changes
- [ ] Custom domains configured (if applicable)
- [ ] SSL certificates active
- [ ] Performance tested (page load < 3s)
- [ ] Mobile responsiveness checked

---

## Troubleshooting

### Backend Issues

#### Build Fails on Railway

**Error:** `No module named 'flask'`

**Solution:** Ensure `requirements.txt` is in project root
```bash
cat requirements.txt | grep flask
# Should show: Flask==3.0.0
```

#### Environment Variables Not Loaded

**Error:** `KeyError: 'AG_URL'`

**Solution:**
1. Check Railway dashboard → Variables
2. Ensure all AG_* variables are set
3. Redeploy after adding variables

#### Health Check Fails

**Error:** `502 Bad Gateway`

**Solution:**
1. Check logs: `railway logs`
2. Ensure Flask app runs:
   ```python
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
   ```
3. Verify `railway.json` has correct start command

### Frontend Issues

#### CORS Errors in Browser

**Error:** `Access-Control-Allow-Origin missing`

**Solution:**
1. Update backend `api/app.py` CORS settings
2. Add Vercel domain to allowed origins
3. Redeploy backend

#### Environment Variables Not Working

**Error:** `NEXT_PUBLIC_API_URL is undefined`

**Solution:**
1. Verify variable name starts with `NEXT_PUBLIC_`
2. Redeploy after adding variables (Vercel doesn't hot-reload env vars)
3. Check browser console:
   ```js
   console.log(process.env.NEXT_PUBLIC_API_URL)
   ```

#### Build Fails on Vercel

**Error:** `Module not found: 'cytoscape'`

**Solution:**
1. Ensure `package.json` has all dependencies
2. Delete `node_modules` and `package-lock.json`
3. Run `npm install` locally to regenerate
4. Commit and redeploy

---

## Alternative Deployment Options

### Backend: Render

**Pros:** Free tier, easy Python support
**Cons:** Slower cold starts than Railway

```bash
# render.yaml
services:
  - type: web
    name: feekg-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT api.app:app
    envVars:
      - key: AG_URL
        value: https://qa-agraph.nelumbium.ai/
      - key: AG_USER
        value: sadmin
      - key: AG_PASS
        sync: false  # Enter in dashboard
```

### Backend: Fly.io

**Pros:** Edge deployment, fast globally
**Cons:** More complex setup

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### Frontend: Netlify

**Pros:** Alternative to Vercel, similar features
**Cons:** Not built specifically for Next.js

```bash
# netlify.toml
[build]
  command = "npm run build"
  publish = ".next"

[[plugins]]
  package = "@netlify/plugin-nextjs"
```

---

## Monitoring & Maintenance

### Railway Monitoring

**Logs:**
```bash
railway logs --tail
```

**Metrics:**
- View in dashboard: CPU, memory, network
- Alerts: Configure in Settings → Notifications

### Vercel Monitoring

**Analytics:**
- Dashboard → Analytics
- Real User Monitoring (RUM)
- Core Web Vitals

**Logs:**
- Dashboard → Deployments → View Function Logs

### AllegroGraph Monitoring

**Check database health:**
```bash
./venv/bin/python scripts/utils/check_feekg_mycatalog.py
```

**Expected output:**
```
✅ Connected to AllegroGraph
📊 Total triples: 59,090
📅 Events: 4,000
👥 Entities: 22
```

---

## Cost Estimates

### Free Tier (Recommended for Testing)

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Railway** | $5/month credit | 500 hours/month |
| **Vercel** | 100GB bandwidth | 100GB/month |
| **AllegroGraph** | Already configured | N/A |

**Total:** $0/month (within free limits)

### Paid Tier (For Production)

| Service | Plan | Cost/Month |
|---------|------|------------|
| **Railway** | Starter | $10 |
| **Vercel** | Pro | $20 |
| **AllegroGraph** | Already configured | $0 (managed) |

**Total:** ~$30/month

---

## Security Best Practices

### Environment Variables

- ✅ Never commit `.env` to Git
- ✅ Use platform-specific secrets management
- ✅ Rotate credentials quarterly
- ✅ Use different credentials for dev/prod

### CORS

- ✅ Whitelist specific domains (not `*`)
- ✅ Update CORS when adding new frontend domains
- ✅ Test CORS in browser DevTools

### HTTPS

- ✅ Always use HTTPS in production
- ✅ Railway/Vercel provide SSL automatically
- ✅ Enforce HTTPS redirects

### API Security

- ✅ Rate limiting (add middleware if needed)
- ✅ Input validation
- ✅ Error messages don't leak sensitive info

---

## Performance Optimization

### Backend (Railway)

**Gunicorn workers:**
```bash
# railway.json
"startCommand": "gunicorn -w 4 -b 0.0.0.0:$PORT api.app:app"
# -w 4 = 4 worker processes
```

**Caching:**
- Add Redis for query caching (Railway add-on)
- Cache expensive SPARQL queries

### Frontend (Vercel)

**Next.js optimization:**
- Use Image component for optimization
- Enable Static Site Generation (SSG) where possible
- Lazy load heavy components (Cytoscape)

**CDN:**
- Vercel's global CDN handles this automatically

---

## Rollback Procedure

### Railway Rollback

```bash
# View deployments
railway status

# Rollback in dashboard
# Dashboard → Deployments → Select previous → Rollback
```

### Vercel Rollback

1. Dashboard → Deployments
2. Find previous working deployment
3. Click "..." → Promote to Production

---

## Next Steps

After successful deployment:

1. **Test thoroughly:** Click through all features
2. **Monitor logs:** Check for errors in first 24 hours
3. **Performance test:** Ensure page loads < 3 seconds
4. **Document URLs:** Save backend/frontend URLs
5. **Share with team:** Provide access to dashboards

---

## Summary

**Deployment URLs:**
- Backend: `https://your-app.up.railway.app`
- Frontend: `https://your-app.vercel.app`

**Key Files:**
- Backend: `railway.json`, `requirements.txt`, `api/app.py`
- Frontend: `next.config.js`, `package.json`

**Critical Settings:**
- Backend: AllegroGraph env vars, CORS domains
- Frontend: `NEXT_PUBLIC_API_URL`

**Time to Deploy:** ~30 minutes for both components

---

**Ready to deploy?** Start with Railway backend, then Vercel frontend. Good luck! 🚀
