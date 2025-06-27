# 🚀 Railway Deployment Guide

## Overview
This guide will help you deploy your Question Paper Generator application to Railway using the **Hobby Plan ($5/month)**.

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **DeepSeek API Key**: Get your API key from [platform.deepseek.com](https://platform.deepseek.com)
3. **Git Repository**: Your code should be in a Git repository

## 🏗️ Architecture on Railway

Your application will be deployed as **3 separate services**:

1. **Backend Service** (FastAPI + Celery Worker)
2. **Redis Service** (Managed Redis instance)
3. **Frontend Service** (React app with Nginx)

## 📁 Files Created for Deployment

- `railway.toml` - Railway configuration
- `Dockerfile.railway` - Optimized backend container
- `frontend/Dockerfile` - Frontend container
- `frontend/nginx.conf` - Nginx configuration
- `Procfile` - Process definitions
- `requirements.railway.txt` - Production dependencies
- `start-railway.sh` - Startup script
- `env.example` - Environment variables template

## 🚀 Step-by-Step Deployment

### Step 1: Create Services on Railway

1. **Create Backend Service**:
   - Go to Railway dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Service name: `question-paper-backend`

2. **Add Redis Service**:
   - In your project, click "New Service"
   - Select "Database" → "Redis"
   - Service name: `redis`

3. **Create Frontend Service**:
   - Click "New Service" → "GitHub Repo"
   - Select same repository
   - Service name: `question-paper-frontend`

### Step 2: Configure Backend Service

1. **Environment Variables**:
   ```bash
   DEEPSEEK_API_KEY=your_api_key_here
   REDIS_URL=${{Redis.REDIS_URL}}
   ENVIRONMENT=production
   DEBUG=false
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```

2. **Build Configuration**:
   - Root Directory: `/`
   - Docker File Path: `Dockerfile.railway`
   - Build Command: (leave empty)
   - Start Command: `./start-railway.sh`

3. **Service Settings**:
   - Memory: 2GB
   - CPU: 2 vCPU
   - Enable Automatic Deployments

### Step 3: Configure Frontend Service

1. **Environment Variables**:
   ```bash
   REACT_APP_API_URL=https://${{question-paper-backend.RAILWAY_PUBLIC_DOMAIN}}
   BACKEND_URL=https://${{question-paper-backend.RAILWAY_PUBLIC_DOMAIN}}
   ```

2. **Build Configuration**:
   - Root Directory: `/frontend`
   - Docker File Path: `Dockerfile`
   - Build Command: (leave empty)
   - Start Command: (leave empty)

### Step 4: Configure Redis Service

Redis will be automatically configured. The `REDIS_URL` will be available as `${{Redis.REDIS_URL}}`.

### Step 5: Deploy

1. **Deploy Services** (in this order):
   - Redis (should deploy automatically)
   - Backend service
   - Frontend service

2. **Monitor Deployments**:
   - Check build logs for any errors
   - Verify health checks pass
   - Test endpoints

### Step 6: Verify Deployment

1. **Backend Health Check**:
   ```
   https://your-backend-service.railway.app/health
   ```

2. **Frontend Access**:
   ```
   https://your-frontend-service.railway.app
   ```

3. **Test Upload**:
   - Try uploading a PDF document
   - Check if question generation works

## 🔧 Troubleshooting

### Common Issues:

1. **Memory Issues**:
   - Reduce model size in code
   - Increase service memory allocation

2. **Redis Connection**:
   - Verify `REDIS_URL` environment variable
   - Check service networking

3. **Model Download Timeout**:
   - The first deployment may take longer
   - Monitor build logs for model downloads

4. **CORS Issues**:
   - Verify frontend environment variables
   - Check API URL configuration

### Debug Commands:

```bash
# Check service logs
railway logs

# Connect to service shell
railway shell

# Restart service
railway up --detach
```

## 📊 Resource Usage (Hobby Plan)

- **Backend**: ~1.5GB RAM, 1-2 vCPU
- **Frontend**: ~512MB RAM, 0.5 vCPU
- **Redis**: ~256MB RAM, 0.25 vCPU

**Total**: ~2.25GB RAM, ~2.75 vCPU (within 8GB/8vCPU limits)

## 💰 Cost Estimation

- **Base Cost**: $5/month (includes $5 usage credit)
- **Estimated Monthly Usage**: $3-7 depending on traffic
- **Total Cost**: Typically $5/month (covered by included credit)

## 🔒 Security Considerations

1. **Environment Variables**: Never commit API keys to git
2. **File Uploads**: Limited to 50MB per file
3. **Rate Limiting**: Consider implementing for production use
4. **HTTPS**: Automatically handled by Railway

## 📝 Post-Deployment

1. **Custom Domain** (optional): Configure in Railway dashboard
2. **Monitoring**: Set up alerts for service health
3. **Backups**: Consider backing up uploaded documents
4. **Updates**: Push to main branch for automatic deployments

## 🆘 Support

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Community**: Railway Discord server
- **Issues**: Check service logs and metrics in Railway dashboard 