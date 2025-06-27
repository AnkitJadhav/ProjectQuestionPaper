# 📋 Railway Deployment Checklist

## Before You Start

- [ ] **Railway Account**: Created and verified
- [ ] **DeepSeek API Key**: Obtained from platform.deepseek.com
- [ ] **Git Repository**: Code pushed to GitHub/GitLab
- [ ] **Files Created**: All deployment files are in place

## Files to Verify

- [ ] `railway.toml` - Railway configuration
- [ ] `Dockerfile.railway` - Backend container
- [ ] `frontend/Dockerfile` - Frontend container  
- [ ] `frontend/nginx.conf` - Nginx configuration
- [ ] `Procfile` - Process definitions
- [ ] `requirements.railway.txt` - Dependencies
- [ ] `start-railway.sh` - Startup script
- [ ] `env.example` - Environment template
- [ ] `RAILWAY_DEPLOYMENT.md` - Full deployment guide

## Step 1: Create Redis Service

- [ ] New Project on Railway
- [ ] Add Redis database service
- [ ] Note the Redis URL variable

## Step 2: Create Backend Service

- [ ] Deploy from GitHub repo
- [ ] Set root directory: `/`
- [ ] Set Dockerfile path: `Dockerfile.railway`
- [ ] Set start command: `./start-railway.sh`

### Backend Environment Variables:
- [ ] `DEEPSEEK_API_KEY=your_key_here`
- [ ] `REDIS_URL=${{Redis.REDIS_URL}}`
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `EMBEDDING_MODEL=all-MiniLM-L6-v2`

### Backend Settings:
- [ ] Memory: 2GB minimum
- [ ] CPU: 2 vCPU minimum
- [ ] Auto-deploy: Enabled

## Step 3: Create Frontend Service

- [ ] New service from same repo
- [ ] Set root directory: `/frontend`
- [ ] Set Dockerfile path: `Dockerfile`

### Frontend Environment Variables:
- [ ] `REACT_APP_API_URL=https://[backend-domain]`
- [ ] `BACKEND_URL=https://[backend-domain]`

## Step 4: Deploy & Test

### Deployment Order:
1. [ ] Redis (automatic)
2. [ ] Backend service
3. [ ] Frontend service

### Testing:
- [ ] Backend health: `https://[backend]/health`
- [ ] Frontend loads: `https://[frontend]/`
- [ ] File upload works
- [ ] Question generation works
- [ ] Download PDF works

## Step 5: Post-Deployment

- [ ] Monitor resource usage
- [ ] Check logs for errors
- [ ] Set up monitoring alerts
- [ ] Configure custom domain (optional)

## 🚨 Common Issues & Solutions

### Build Failures:
- Check Dockerfile paths
- Verify all files are committed
- Check build logs for specific errors

### Memory Issues:
- Increase service memory allocation
- Monitor usage in Railway dashboard

### Redis Connection:
- Verify `REDIS_URL` environment variable
- Check service networking between services

### CORS Errors:
- Verify frontend `REACT_APP_API_URL`
- Check backend CORS configuration

## 💡 Pro Tips

1. **Monitor First Deploy**: Takes 5-10 minutes for ML models to download
2. **Check Logs**: Use Railway CLI or dashboard for debugging
3. **Resource Monitoring**: Keep an eye on memory/CPU usage
4. **Gradual Testing**: Test each service individually first

## 📞 Support Resources

- **Railway Docs**: docs.railway.app
- **Railway Discord**: railway.app/discord
- **This Project's Guide**: `RAILWAY_DEPLOYMENT.md` 