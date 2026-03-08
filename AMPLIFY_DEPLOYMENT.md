# AWS Amplify Deployment Guide (Simplest Option)

## Why Amplify?

- ✅ Works with your existing Flask code (no changes needed)
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Permanent URL
- ✅ Takes 15-20 minutes
- ✅ No complex configuration

---

## Prerequisites

1. AWS Account
2. GitHub account (free)
3. Git installed on your computer

---

## Step 1: Push Your Code to GitHub

```bash
# Navigate to your project
cd ~/Documents/Sabiha\ Projects/3P-apps

# Initialize git (if not already done)
git init

# Create .gitignore file
cat > .gitignore << EOF
venv/
__pycache__/
*.pyc
.env
.DS_Store
*.md
EOF

# Add all files
git add .

# Commit
git commit -m "Initial commit"

# Create a new repository on GitHub
# Go to: https://github.com/new
# Repository name: connect-queue-monitor
# Make it Private
# Don't initialize with README

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/connect-queue-monitor.git
git branch -M main
git push -u origin main
```

---

## Step 2: Create amplify.yml Configuration

Create a file called `amplify.yml` in your project root:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - pip install -r requirements.txt
    build:
      commands:
        - echo "Build completed"
  artifacts:
    baseDirectory: /
    files:
      - '**/*'
  cache:
    paths:
      - venv/**/*
```

---

## Step 3: Deploy to Amplify

### Option A: Using AWS Console (Easiest)

1. **Go to AWS Amplify Console**: https://console.aws.amazon.com/amplify/

2. **Click "New app" → "Host web app"**

3. **Connect to GitHub**:
   - Select GitHub
   - Authorize AWS Amplify
   - Select your repository: `connect-queue-monitor`
   - Select branch: `main`

4. **Configure build settings**:
   - App name: `connect-queue-monitor`
   - Environment: `production`
   - Build settings: (auto-detected from amplify.yml)

5. **Add environment variables**:
   Click "Advanced settings" and add:
   ```
   AWS_REGION=us-east-1
   CONNECT_INSTANCE_ID=6091de37-993e-45c8-9637-e9e3a0af5b23
   CONNECT_INSTANCE_URL=https://unt-sample-cicd-instance-sab-test.my.connect.aws
   FLASK_SECRET_KEY=your-secret-key-here
   FLASK_DEBUG=False
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_SESSION_TOKEN=your-session-token
   ```

6. **Click "Save and deploy"**

7. **Wait 5-10 minutes** for deployment

8. **Get your URL**: 
   - Will be something like: `https://main.d1234abcd.amplifyapp.com`

### Option B: Using Amplify CLI

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Configure Amplify
amplify configure

# Initialize Amplify in your project
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

---

## Step 4: Update Amazon Connect

1. Go to Amazon Connect Console
2. Navigate to: Channels → Agent applications
3. Click on "Queue Monitor"
4. Update Application URL with your Amplify URL
5. Update Allowed origins with your Amplify URL
6. Save changes

---

## Step 5: Test

1. Log into Amazon Connect as an agent
2. Open Queue Monitor app
3. Should load directly without warning page
4. Verify queues display correctly

---

## Updating Your App

When you make changes:

```bash
# Commit changes
git add .
git commit -m "Updated feature"
git push

# Amplify automatically redeploys!
```

---

## Cost

**Free Tier:**
- 1000 build minutes/month
- 15 GB storage
- 15 GB bandwidth/month

**After Free Tier:**
- ~$0.01 per build minute
- ~$0.023 per GB storage
- ~$0.15 per GB bandwidth

**Estimated cost for your app:** $0-5/month

---

## Troubleshooting

### Build fails
- Check build logs in Amplify console
- Verify requirements.txt is correct
- Check environment variables are set

### App doesn't load
- Verify Flask app starts correctly
- Check that port 8080 is used
- Review application logs

---

## Alternative: Even Simpler with Render.com

If AWS seems complex, try Render.com (also free):

1. Go to: https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Configure:
   - Name: connect-queue-monitor
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run.py`
6. Add environment variables
7. Deploy

Render gives you: `https://connect-queue-monitor.onrender.com`

---

## My Recommendation

**For your demo in 23 days:**

1. **Today/This Week**: Try Render.com (simplest, 10 minutes)
2. **If Render doesn't work**: Try AWS Amplify (20 minutes)
3. **If both fail**: Get ngrok paid plan ($8/month, works immediately)

All three options eliminate the warning page and give you a permanent URL.
