# AWS Elastic Beanstalk Deployment Guide

## Why Deploy to AWS?

**Problems with free ngrok:**
- Warning page appears in iframe (can't be bypassed)
- URL changes every restart
- Not suitable for demos or production

**Benefits of AWS:**
- ✅ No warning page
- ✅ Permanent URL
- ✅ Free tier available (12 months)
- ✅ Always available (24/7)
- ✅ Professional deployment

---

## Prerequisites

1. AWS Account (free tier eligible)
2. AWS CLI installed
3. EB CLI installed

---

## Step 1: Install AWS CLI and EB CLI

```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: us-east-1
# Enter output format: json

# Install EB CLI
pip install awsebcli
```

---

## Step 2: Prepare Your Application

Create a file called `application.py` in your project root:

```bash
# This file is required by Elastic Beanstalk
# It imports your Flask app
from run import app as application

if __name__ == '__main__':
    application.run()
```

Create `.ebignore` file:

```
venv/
__pycache__/
*.pyc
.env
.DS_Store
*.md
tests/
.git/
.kiro/
```

---

## Step 3: Initialize Elastic Beanstalk

```bash
# Navigate to your project directory
cd ~/Documents/Sabiha\ Projects/3P-apps

# Initialize EB
eb init

# Follow the prompts:
# 1. Select region: us-east-1
# 2. Application name: connect-queue-monitor
# 3. Platform: Python
# 4. Platform version: Python 3.9
# 5. SSH: No (unless you need it)
```

---

## Step 4: Create Environment

```bash
# Create environment (this takes 5-10 minutes)
eb create connect-queue-monitor-env

# Wait for deployment to complete
```

---

## Step 5: Set Environment Variables

```bash
# Set your AWS credentials and Connect instance details
eb setenv \
  AWS_REGION=us-east-1 \
  CONNECT_INSTANCE_ID=6091de37-993e-45c8-9637-e9e3a0af5b23 \
  CONNECT_INSTANCE_URL=https://unt-sample-cicd-instance-sab-test.my.connect.aws \
  FLASK_SECRET_KEY=your-secret-key-here \
  FLASK_DEBUG=False \
  AWS_ACCESS_KEY_ID=your-access-key \
  AWS_SECRET_ACCESS_KEY=your-secret-key \
  AWS_SESSION_TOKEN=your-session-token
```

---

## Step 6: Get Your Application URL

```bash
# Get your application URL
eb status

# Look for "CNAME:" - this is your permanent URL
# Example: connect-queue-monitor-env.us-east-1.elasticbeanstalk.com
```

Your permanent URL will be:
```
https://connect-queue-monitor-env.us-east-1.elasticbeanstalk.com
```

---

## Step 7: Update Amazon Connect

1. Go to Amazon Connect Console
2. Navigate to: Channels → Agent applications
3. Click on "Queue Monitor"
4. Update Application URL with your new AWS URL
5. Update Allowed origins with your AWS URL
6. Save changes

---

## Step 8: Test

1. Log into Amazon Connect as an agent
2. Open Queue Monitor app
3. Should load directly without any warning page
4. Verify queues display correctly

---

## Updating Your Application

When you make changes to your code:

```bash
# Deploy updates
eb deploy

# Check status
eb status

# View logs if needed
eb logs
```

---

## Cost Estimate

**Free Tier (First 12 months):**
- 750 hours/month of t2.micro instance (enough for 24/7)
- 5 GB of storage
- 20 GB of bandwidth

**After Free Tier:**
- ~$15-20/month for t2.micro instance running 24/7
- Can reduce costs by stopping when not in use

---

## Troubleshooting

### Application won't start
```bash
# Check logs
eb logs

# SSH into instance (if enabled)
eb ssh
```

### Environment variables not working
```bash
# Verify environment variables
eb printenv

# Update if needed
eb setenv KEY=value
```

### Need to restart
```bash
# Restart application
eb restart
```

---

## Alternative: Quick AWS Deployment with Amplify

If Elastic Beanstalk seems complex, you can also use AWS Amplify:

1. Push your code to GitHub
2. Go to AWS Amplify Console
3. Connect your GitHub repository
4. Amplify will auto-deploy
5. Get permanent URL

---

## Recommendation

For your demo in 23 days:

**Quick solution (today):** Get ngrok paid plan ($8) - 5 minutes setup
**Best solution (this week):** Deploy to AWS - 1-2 hours setup, free for 12 months

Both eliminate the warning page and give you a permanent URL.
