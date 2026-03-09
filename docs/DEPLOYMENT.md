# Deployment Guide - Elastic Beanstalk

## 📦 Complete Deployment Guide

This guide walks you through deploying the Amazon Connect Queue Monitor to AWS Elastic Beanstalk.

## Prerequisites

Before you start, make sure you have:

1. ✅ **AWS Account** with admin access
2. ✅ **Amazon Connect Instance** set up
3. ✅ **AWS CLI** installed (optional, but helpful)
4. ✅ **Git** installed (for version control)
5. ✅ **Python 3.9+** installed locally (for testing)

## Step 1: Prepare AWS Credentials

### Create IAM User

1. Go to **IAM Console**: https://console.aws.amazon.com/iam
2. Click **Users** → **Add users**
3. Username: `connect-queue-monitor-user`
4. Access type: **Programmatic access**
5. Attach policies:
   - `AmazonConnectReadOnlyAccess`
   - `AWSElasticBeanstalkFullAccess`
6. Click **Create user**
7. **Save credentials**:
   - Access Key ID
   - Secret Access Key

### Get Amazon Connect Details

1. Go to **Amazon Connect Console**: https://console.aws.amazon.com/connect
2. Click your instance
3. Copy:
   - **Instance ID**: Found in instance ARN (last part after `/instance/`)
   - **Instance URL**: Your Connect URL (e.g., `https://your-instance.my.connect.aws`)

## Step 2: Configure Environment Variables

### Create `.env` File

Copy `.env.example` to `.env` and fill in your values:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=  # Leave empty unless using temporary credentials

# Amazon Connect Configuration
CONNECT_INSTANCE_ID=your-instance-id-here
CONNECT_INSTANCE_URL=https://your-instance.my.connect.aws

# Flask Configuration
FLASK_SECRET_KEY=your-random-secret-key-here
FLASK_ENV=production
```

### Generate Flask Secret Key

Run this command to generate a secure random key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as your `FLASK_SECRET_KEY`.

## Step 3: Test Locally

Before deploying, test the app locally:

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
# Make sure .env file is configured
python3 run.py
```

Visit `http://localhost:8080` and test:
- ✅ Login with your Amazon Connect username
- ✅ See your queues
- ✅ Click "Refresh Queues" button
- ✅ Verify metrics update

If everything works, proceed to deployment!

## Step 4: Create Deployment Package

### Option A: Using Script (Recommended)

```bash
# Make script executable
chmod +x scripts/create_deployment_package.sh

# Create deployment package
./scripts/create_deployment_package.sh
```

This creates `deployment.zip` with all necessary files.

### Option B: Manual Zip

```bash
zip -r deployment.zip \
  app/ \
  config/ \
  run.py \
  requirements.txt \
  Procfile \
  .ebextensions/ \
  .platform/ \
  -x "*.pyc" -x "*__pycache__*" -x "*.DS_Store" -x ".env"
```

**Important**: Do NOT include `.env` file in the zip (contains secrets)!

## Step 5: Deploy to Elastic Beanstalk

### Create Elastic Beanstalk Application

1. Go to **Elastic Beanstalk Console**: https://console.aws.amazon.com/elasticbeanstalk
2. Click **Create Application**
3. Fill in details:
   - **Application name**: `connect-queue-monitor`
   - **Platform**: Python
   - **Platform branch**: Python 3.9 running on 64bit Amazon Linux 2
   - **Application code**: Upload your code
   - **Upload**: Select `deployment.zip`
4. Click **Create application**

Wait 5-10 minutes for deployment to complete.

### Configure Environment Variables

1. In Elastic Beanstalk console, click your environment
2. Click **Configuration** → **Software** → **Edit**
3. Scroll to **Environment properties**
4. Add these variables (from your `.env` file):
   - `AWS_REGION`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `CONNECT_INSTANCE_ID`
   - `CONNECT_INSTANCE_URL`
   - `FLASK_SECRET_KEY`
   - `FLASK_ENV` = `production`
5. Click **Apply**

Wait for environment to update (~3 minutes).

### Test Elastic Beanstalk URL

1. Copy your environment URL (e.g., `http://connect-queue-monitor-env.eba-xxxxx.us-east-1.elasticbeanstalk.com`)
2. Visit the URL in your browser
3. Test login and dashboard

If it works, proceed to CloudFront setup!

## Step 6: Set Up CloudFront (HTTPS)

Amazon Connect requires HTTPS for embedding. CloudFront provides this.

### Create CloudFront Distribution

1. Go to **CloudFront Console**: https://console.aws.amazon.com/cloudfront
2. Click **Create Distribution**
3. Configure:
   - **Origin domain**: Your Elastic Beanstalk URL (without http://)
   - **Protocol**: HTTP only
   - **Viewer protocol policy**: Redirect HTTP to HTTPS
   - **Allowed HTTP methods**: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
   - **Cache policy**: CachingDisabled
   - **Origin request policy**: AllViewer
4. Click **Create distribution**

Wait 10-15 minutes for distribution to deploy.

### Get CloudFront URL

1. Copy your CloudFront domain (e.g., `https://d1234567890.cloudfront.net`)
2. Test in browser
3. Verify HTTPS works

## Step 7: Add to Amazon Connect

### Create Third-Party Application

1. Go to **Amazon Connect Console**
2. Click your instance → **Third-party applications**
3. Click **Add application**
4. Fill in:
   - **Application name**: Queue Monitor
   - **Application URL**: Your CloudFront URL
   - **Application type**: Custom
   - **Display name**: My Queue Dashboard
   - **Description**: View my assigned queues and performance metrics
5. Click **Add application**

### Configure Application Settings

1. Click the application you just created
2. Configure:
   - **Contact scope**: Cross contacts (stays visible across calls)
   - **Width**: 400-800px (your preference)
   - **Height**: 600-800px (your preference)
3. Click **Save**

### Add to Agent Workspace

1. Go to **Agent applications** in Amazon Connect
2. Add "Queue Monitor" to agent workspace layout
3. Save layout

### Test in Amazon Connect

1. Log in to Amazon Connect as an agent
2. Open CCP (Contact Control Panel)
3. Look for "My Queue Dashboard" panel
4. Verify:
   - ✅ App loads automatically
   - ✅ Agent is auto-detected (no manual login)
   - ✅ Queues display correctly
   - ✅ Metrics auto-refresh every 15 seconds

## Step 8: Update Deployment (Future Changes)

When you make code changes:

### 1. Create New Deployment Package

```bash
./scripts/create_deployment_package.sh
```

### 2. Upload to Elastic Beanstalk

1. Go to Elastic Beanstalk console
2. Click your environment
3. Click **Upload and deploy**
4. Select new `deployment.zip`
5. Version label: `v1.1` (increment version)
6. Click **Deploy**

Wait 3-5 minutes for deployment.

### 3. Invalidate CloudFront Cache (If Needed)

Only needed if you changed frontend files (HTML, CSS, JS, images):

1. Go to CloudFront console
2. Click your distribution
3. Click **Invalidations** tab
4. Click **Create invalidation**
5. Object paths: `/*` (invalidate everything)
6. Click **Create invalidation**

Wait 1-2 minutes for invalidation to complete.

## Monitoring and Logs

### View Application Logs

**Option 1: Elastic Beanstalk Console**
1. Go to your environment
2. Click **Logs** → **Request Logs** → **Last 100 Lines**
3. Download and view

**Option 2: CloudWatch Logs**
1. Go to CloudWatch console
2. Click **Log groups**
3. Find `/aws/elasticbeanstalk/connect-queue-monitor-env/`
4. View logs

### Check Application Health

1. Go to Elastic Beanstalk console
2. Click your environment
3. Check **Health** status (should be "Ok" in green)
4. If degraded, check logs for errors

### Monitor Costs

1. Go to **AWS Cost Explorer**
2. Filter by service:
   - Elastic Beanstalk: ~$15/month
   - CloudFront: ~$1-2/month
   - Amazon Connect API calls: ~$0.38/agent/month
3. Set up billing alerts if desired

## Troubleshooting

### App Won't Load

**Check**:
1. Elastic Beanstalk health status
2. Environment variables are set correctly
3. CloudFront distribution is deployed
4. Security groups allow HTTP traffic

**Fix**:
- Check logs for errors
- Verify AWS credentials are valid
- Ensure Connect instance ID is correct

### Login Fails

**Check**:
1. Agent username exists in Amazon Connect
2. AWS credentials have Connect permissions
3. Connect instance ID is correct

**Fix**:
- Test AWS credentials with AWS CLI
- Verify agent exists: `aws connect list-users --instance-id YOUR_ID`

### Metrics Don't Update

**Check**:
1. Browser console for JavaScript errors (F12)
2. Network tab shows successful API calls
3. CloudFront cache is not blocking updates

**Fix**:
- Hard refresh browser (Ctrl+Shift+R)
- Invalidate CloudFront cache
- Check Elastic Beanstalk logs

### Auto-Refresh Not Working

**Check**:
1. Browser console shows "🔄 Starting auto-refresh" message
2. No JavaScript errors in console
3. Tab is visible (auto-refresh pauses when hidden)

**Fix**:
- Hard refresh browser
- Check if JavaScript is enabled
- Try different browser

### Session Expires Too Quickly

**Check**:
1. `FLASK_SECRET_KEY` is set in environment variables
2. Cookies are enabled in browser
3. CloudFront is forwarding cookies

**Fix**:
- Verify CloudFront origin request policy is "AllViewer"
- Check browser cookie settings
- Try incognito mode to test

## Security Best Practices

### Protect AWS Credentials

1. ✅ Never commit `.env` file to Git
2. ✅ Use IAM user with minimal permissions
3. ✅ Rotate credentials every 90 days
4. ✅ Enable MFA on AWS account
5. ✅ Use AWS Secrets Manager for production (optional)

### Secure Flask App

1. ✅ Use strong `FLASK_SECRET_KEY` (32+ characters)
2. ✅ Set `FLASK_ENV=production` (never `development`)
3. ✅ Keep dependencies updated (`pip install --upgrade`)
4. ✅ Monitor logs for suspicious activity

### Network Security

1. ✅ Use HTTPS only (CloudFront enforces this)
2. ✅ Restrict CORS to Amazon Connect domains only
3. ✅ Use security headers (already configured)
4. ✅ Keep Elastic Beanstalk platform updated

## Cost Optimization

### Current Costs (~$17/month)

- **Elastic Beanstalk**: $15/month (t3.micro)
- **CloudFront**: $1-2/month
- **Connect API calls**: $0.38/agent/month

### Ways to Reduce Costs

1. **Use Reserved Instance**: Save 30-40% on EC2 costs
2. **Increase refresh interval**: 30s instead of 15s (saves 50% API calls)
3. **Use Spot Instance**: Save up to 70% (but may be interrupted)
4. **Optimize CloudFront**: Increase cache TTL for static files

### When to Scale Up

- **50-100 agents**: Upgrade to t3.small ($30/month)
- **100-500 agents**: Use t3.medium + load balancer ($60/month)
- **500+ agents**: Consider Lambda migration (see `docs/LAMBDA_ALTERNATIVE.md`)

## Backup and Disaster Recovery

### Backup Strategy

1. **Code**: Stored in GitHub (version controlled)
2. **Configuration**: Environment variables documented
3. **Deployment package**: Keep last 3 versions

### Disaster Recovery

If Elastic Beanstalk environment fails:

1. Create new environment from saved deployment package
2. Configure environment variables
3. Update CloudFront origin to new environment
4. Test and verify

**Recovery Time**: ~15 minutes

## Next Steps

1. ✅ Deploy to Elastic Beanstalk
2. ✅ Set up CloudFront
3. ✅ Add to Amazon Connect
4. ✅ Test with agents
5. ✅ Monitor costs and performance
6. ✅ Set up billing alerts
7. ✅ Document any custom configurations
8. ✅ Train agents on how to use the dashboard

## Support

If you need help:

1. Check `docs/TROUBLESHOOTING.md`
2. Check `docs/API_REFERENCE.md`
3. Review code comments (every file is documented)
4. Check AWS documentation
5. Contact AWS Support (if you have a support plan)

## Additional Resources

- [AWS Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [Amazon Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
