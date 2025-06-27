# 🚀 Fresh Railway Deployment Checklist

## ✅ Step-by-Step Guide

### **Step 1: Create New Railway Service**
- [ ] Go to [railway.app/dashboard](https://railway.app/dashboard)
- [ ] Click "New Project" OR open existing ProjectQuestionPaper project
- [ ] Click "+ New Service"
- [ ] Select "GitHub Repo"
- [ ] Choose "AnkitJadhav/ProjectQuestionPaper"
- [ ] Click "Deploy"

### **Step 2: Configure Service Settings**
- [ ] **Root Directory:** `/` (forward slash)
- [ ] **Build Command:** (leave empty)
- [ ] **Start Command:** (leave empty)
- [ ] **Domain:** Copy the generated Railway URL

### **Step 3: Add Environment Variables**
Go to your service → Variables tab → Add these:

- [ ] **Variable Name:** `ENVIRONMENT`  
      **Value:** `production`

- [ ] **Variable Name:** `FORCE_FULL_MODE`  
      **Value:** `true`

### **Step 4: Wait for Deployment**
- [ ] Watch deployment logs (5-10 minutes)
- [ ] Look for "Build successful" message
- [ ] Check service status shows "Active"

### **Step 5: Get Your New URL**
- [ ] Copy Railway URL from "Domains" section
- [ ] URL format: `https://web-production-xxxx.up.railway.app`

### **Step 6: Update Local Scripts**
Run in your terminal:
```bash
python update_url.py
```
- [ ] Enter your new Railway URL
- [ ] Scripts will auto-update

### **Step 7: Test Deployment**
```bash
python quick_test.py
```

Expected result:
- [ ] Status: 200 ✅
- [ ] Mode: "full" ✅ (not "minimal")
- [ ] All endpoints working ✅

### **Step 8: Start Using Your App**
```bash
python interact_deployed.py
```

### **🔧 If Something Goes Wrong:**

#### **Build Fails:**
- Check GitHub repo is accessible
- Verify Dockerfile.production exists
- Check Railway build logs

#### **App Shows "minimal" mode:**
- Add environment variables exactly as shown
- Redeploy service
- Wait 5-10 minutes

#### **404 Errors:**
- Service might still be deploying
- Check Railway service status
- Verify domain is active

### **🎯 Success Indicators:**

Your deployment is successful when:
- ✅ Railway dashboard shows service "Active"
- ✅ URL returns `{"status": "running", "mode": "full"}`
- ✅ `/documents` endpoint works (not 404)
- ✅ Upload functionality available
- ✅ ML processing ready

### **📱 Quick Commands After Setup:**

Test connection:
```bash
python quick_test.py
```

Interactive menu:
```bash
python interact_deployed.py
```

Upload a PDF:
```bash
# Use option 4 in interactive menu
# OR direct API call
```

Generate papers:
```bash
# Use option 6 in interactive menu
```

---

## 🆘 **Need Help?**

If you get stuck:
1. Check Railway deployment logs
2. Verify environment variables are set
3. Run `python update_url.py` to update URLs
4. Test with `python quick_test.py`

Your Question Paper Generator will be fully functional once deployed! 🎉 