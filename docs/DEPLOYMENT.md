# FE-EKG Deployment Guide

## Overview

This guide will help you deploy the FE-EKG system to production using:
- **Backend**: Railway.app (Flask + AllegroGraph)
- **Frontend**: Vercel (Next.js)

## Prerequisites

- GitHub account
- Railway account (sign up at https://railway.app)
- Vercel account (sign up at https://vercel.com)
- AllegroGraph credentials (already configured)

## Part 1: Deploy Backend to Railway

### Step 1: Push Code to GitHub

Ensure all backend code is pushed to the repository:
```bash
cd /path/to/feekg
git add .
git commit -m "Prepare backend for Railway deployment"
git push origin main
```

### Step 2: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your `FEEKG-backend` (or `FEEKG_2.0`) repository
4. Railway will auto-detect the Python project

### Step 3: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

```
GRAPH_BACKEND=allegrograph
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_REPO=Event_risk
FLASK_ENV=production
```

**Important**: Do NOT set `PORT` - Railway sets this automatically.

### Step 4: Deploy

Railway will automatically:
1. Install dependencies from `requirements.txt`
2. Start the app using the `Procfile`
3. Assign a public URL (e.g., `https://feekg-production.up.railway.app`)

### Step 5: Test Backend

Once deployed, test the API:
```bash
curl https://your-railway-app.up.railway.app/health
curl https://your-railway-app.up.railway.app/api/stats
```

You should get JSON responses confirming the API is working.

## Part 2: Deploy Frontend to Vercel

### Step 1: Push Frontend to GitHub

```bash
cd /path/to/feekg-frontend
git add .
git commit -m "Prepare frontend for Vercel deployment"
git push origin main
```

### Step 2: Import Project to Vercel

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your `FEEKG-Frontend` repository
4. Vercel will auto-detect it's a Next.js project

### Step 3: Configure Environment Variables

In the Vercel import screen, add these environment variables:

```
NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app
NEXT_PUBLIC_DEFAULT_PAGE_SIZE=100
NEXT_PUBLIC_MAX_NODES=1000
```

**Replace `your-railway-app.up.railway.app`** with your actual Railway URL from Part 1.

### Step 4: Deploy

Click "Deploy" - Vercel will:
1. Build your Next.js app
2. Deploy to global CDN
3. Assign a URL (e.g., `https://feekg-frontend.vercel.app`)

### Step 5: Test Frontend

Open your Vercel URL in a browser. You should see:
- Accurate statistics from AllegroGraph
- Working "Explore Graph" and "Timeline" links
- Working "Documentation" link

## Troubleshooting

### Backend Issues

**Problem**: Railway build fails
- Check build logs in Railway dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version compatibility

**Problem**: API returns 500 errors
- Check Railway logs for error messages
- Verify AllegroGraph credentials in environment variables
- Test connection to AllegroGraph from Railway

### Frontend Issues

**Problem**: Can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS is enabled in backend (already configured)
- Test backend URL directly with curl

**Problem**: Build fails on Vercel
- Check build logs in Vercel dashboard
- Ensure all dependencies are in `package.json`
- Verify Node.js version compatibility

## Custom Domain (Optional)

### Railway Custom Domain

1. In Railway dashboard → Settings → Domains
2. Add your custom domain (e.g., `api.feekg.com`)
3. Update DNS records as instructed

### Vercel Custom Domain

1. In Vercel dashboard → Project Settings → Domains
2. Add your custom domain (e.g., `feekg.com`)
3. Update DNS records as instructed
4. Update `NEXT_PUBLIC_API_URL` to match Railway custom domain

## Environment Variables Reference

### Backend (Railway)

| Variable | Description | Example |
|----------|-------------|---------|
| `GRAPH_BACKEND` | Database backend to use | `allegrograph` |
| `AG_URL` | AllegroGraph server URL | `https://qa-agraph.nelumbium.ai/` |
| `AG_USER` | AllegroGraph username | `sadmin` |
| `AG_PASS` | AllegroGraph password | `your_password` |
| `AG_REPO` | AllegroGraph repository | `Event_risk` |
| `FLASK_ENV` | Flask environment | `production` |

### Frontend (Vercel)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://feekg.up.railway.app` |
| `NEXT_PUBLIC_DEFAULT_PAGE_SIZE` | Default pagination size | `100` |
| `NEXT_PUBLIC_MAX_NODES` | Max nodes in graph | `1000` |

## Continuous Deployment

Both Railway and Vercel support automatic deployments:

- **Railway**: Automatically redeploys when you push to `main` branch
- **Vercel**: Automatically redeploys when you push to `main` branch
- **Preview Deployments**: Both create preview URLs for PRs

## Monitoring

### Railway

- View logs: Dashboard → Deployments → Logs
- Monitor metrics: Dashboard → Metrics (CPU, Memory, Network)

### Vercel

- View analytics: Dashboard → Analytics
- Monitor performance: Dashboard → Speed Insights

## Cost Estimate

### Railway Free Tier

- $5 free credit per month
- Should cover development/demo usage
- Upgrade to Hobby ($5/month) or Pro ($20/month) for production

### Vercel Free Tier

- Unlimited personal projects
- 100 GB bandwidth per month
- Should be sufficient for most use cases

## Support

If you encounter issues:

1. Check deployment logs in Railway/Vercel dashboards
2. Verify environment variables are set correctly
3. Test backend and frontend independently
4. Contact support:
   - Railway: https://railway.app/help
   - Vercel: https://vercel.com/support

---

**Last Updated**: 2025-11-16
**Status**: Production Ready
