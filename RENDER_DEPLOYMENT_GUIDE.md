# 🚀 Render.com Deployment Guide

## ✅ Why Render.com is Perfect for Our App

- **7GB image limit** (our app is only ~2GB)
- **FREE tier** with 750 hours/month
- **No Unicode bugs** like Railway has
- **Better reliability** and uptime
- **Excellent Docker support**

## 🎯 Quick Deploy Steps

### 1. Go to Render.com
Visit: https://render.com

### 2. Sign Up with GitHub
- Click "Get Started for Free"
- Choose "Sign up with GitHub"
- Authorize Render to access your repositories

### 3. Create New Web Service
- Click "New +" button
- Select "Web Service"
- Connect your GitHub account if not already connected

### 4. Select Repository
- Find and select: `AnkitJadhav/ProjectQuestionPaper`
- Click "Connect"

### 5. Configure Service Settings

**Basic Settings:**
- **Name**: `question-paper-generator`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Runtime**: `Docker`

**Build Settings:**
- **Dockerfile Path**: `Dockerfile.render`
- **Build Command**: Leave empty
- **Start Command**: Leave empty (Docker handles this)

### 6. Environment Variables
Click "Advanced" and add these environment variables:

```
ENVIRONMENT = production
FORCE_FULL_MODE = true
```

### 7. Instance Type
- Select **Free** (sufficient for our app)

### 8. Deploy!
- Click "Create Web Service"
- Wait 8-10 minutes for deployment

## 🎉 Your App Will Be Live!

Once deployed, you'll get a URL like:
`https://question-paper-generator.onrender.com`

## 🔧 Features That Will Work

✅ **Full ML Question Generation**
✅ **PDF Upload & Processing**  
✅ **Document Management**
✅ **Question Paper Export**
✅ **All API endpoints**

## 🚀 Advantages Over Railway

- ✅ **No size limits** (7GB vs 4GB)
- ✅ **No Unicode bugs**
- ✅ **Better reliability**
- ✅ **Faster deployments**
- ✅ **FREE tier**

## 📊 Performance

- **Build time**: 8-10 minutes
- **Image size**: ~2GB (optimized)
- **Startup time**: 2-3 minutes (ML libraries install at runtime)
- **Memory usage**: ~1.5GB under load

## 🛠️ Troubleshooting

If deployment fails:
1. Check logs in Render dashboard
2. Verify environment variables are set
3. Ensure `Dockerfile.production` is selected

## 🎯 Testing Your Deployment

Once live, test these endpoints:
- `GET /` - Basic health check
- `GET /health` - Detailed status
- `POST /upload` - Upload PDF
- `POST /generate` - Generate questions

Your app is now production-ready! 🚀 