# Railway Recovery Guide

## If Current Service is Broken:

### Option 1: Redeploy Current Service
1. Go to Railway Dashboard → ProjectQuestionPaper
2. Click your backend service
3. Go to "Deployments" tab
4. Click "Redeploy" on latest deployment

### Option 2: Create Fresh Service
1. In Railway Dashboard → ProjectQuestionPaper
2. Click "+ New Service"
3. Select "GitHub Repo"
4. Connect: AnkitJadhav/ProjectQuestionPaper
5. Set these settings:
   - Root Directory: /
   - Build Command: (leave empty)
   - Start Command: (leave empty)

### Option 3: Quick Fix URL
Try different URL patterns:
- https://projectquestionpaper-production.up.railway.app
- https://projectquestionpaper.up.railway.app  
- https://web-production-xxxx.up.railway.app

### Environment Variables to Add:
```
ENVIRONMENT = production
FORCE_FULL_MODE = true
PORT = ${{RAILWAY_PORT}}
```

### Check Service Status:
Look for these in Railway dashboard:
- ✅ Service Status: "Active" 
- ✅ Latest Deploy: "Success"
- ✅ Domain: Shows public URL
- ✅ Logs: No errors

### Test Commands:
```bash
python quick_test.py
python interact_deployed.py
``` 