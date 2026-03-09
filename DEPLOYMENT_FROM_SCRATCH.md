# Deploy Connect Queue Monitor - Complete Guide

This guide walks you through deploying the Connect Queue Monitor application to a **brand new AWS account** and **new Amazon Connect instance** from scratch.

**Time Required**: 2-3 hours  
**Skill Level**: Beginner-friendly (step-by-step instructions)

---

## 📋 Table of Contents

**Click any step to jump directly to it:**

1. [Prerequisites](#prerequisites) - Tools and accounts you need
2. [Step 1: Set Up AWS Account](#step-1-set-up-aws-account) - Create AWS account and IAM user
3. [Step 2: Create Amazon Connect Instance](#step-2-create-amazon-connect-instance) - Set up Connect instance and test agents
4. [Step 3: Configure IAM Permissions](#step-3-configure-iam-permissions) - Set up permissions for the app
5. [Step 4: Set Up Local Development Environment](#step-4-set-up-local-development-environment) - Clone repo and install dependencies
6. [Step 5: Configure Application](#step-5-configure-application) - Set environment variables
7. [Step 6: Test Locally](#step-6-test-locally) - Run and test on your computer
8. [Step 7: Deploy to Elastic Beanstalk](#step-7-deploy-to-elastic-beanstalk) - Deploy to AWS
9. [Step 8: Set Up CloudFront for HTTPS](#step-8-set-up-cloudfront-for-https) - Enable HTTPS access
10. [Step 9: Add to Amazon Connect](#step-9-add-to-amazon-connect) - Integrate with agent workspace
11. [Step 10: Test End-to-End](#step-10-test-end-to-end) - Verify everything works
12. [Troubleshooting](#troubleshooting) - Common issues and solutions

---

## Prerequisites

### What You Need

- **AWS Account** (new or existing)
- **Credit card** for AWS billing (free tier available)
- **Computer** with:
  - macOS, Windows, or Linux
  - Internet connection
  - Terminal/Command Prompt access
- **Basic knowledge** of:
  - Using terminal/command line
  - AWS console navigation (we'll guide you)

### Tools to Install

1. **Python 3.11+**
   - macOS: `brew install python3`
   - Windows: Download from [python.org](https://www.python.org/downloads/)
   - Linux: `sudo apt-get install python3`

2. **Git**
   - macOS: `brew install git`
   - Windows: Download from [git-scm.com](https://git-scm.com/)
   - Linux: `sudo apt-get install git`

3. **AWS CLI**
   - All platforms: Follow [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

4. **Elastic Beanstalk CLI**
   ```bash
   pip install awsebcli
   ```

---

## Step 1: Set Up AWS Account

### 1.1 Create AWS Account (if new)

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click **"Create an AWS Account"**
3. Enter email, password, and account name
4. Provide contact information
5. Enter payment information (credit card)
6. Verify phone number
7. Choose **"Basic Support - Free"** plan
8. Complete sign-up

**Cost Note**: This application uses AWS Free Tier where possible. Expected cost: $17-37/month depending on usage.

### 1.2 Create IAM User for Deployment

1. Log into [AWS Console](https://console.aws.amazon.com)
2. Search for **"IAM"** in the top search bar
3. Click **"Users"** in left sidebar
4. Click **"Create user"**
5. Enter username: `connect-queue-monitor-deployer`
6. Click **"Next"**
7. Select **"Attach policies directly"**
8. Search and select these policies:
   - `AmazonConnect_FullAccess`
   - `AWSElasticBeanstalkFullAccess`
   - `CloudFrontFullAccess`
   - `IAMFullAccess` (needed to create roles)
9. Click **"Next"** → **"Create user"**

### 1.3 Create Access Keys

1. Click on the user you just created
2. Go to **"Security credentials"** tab
3. Scroll to **"Access keys"**
4. Click **"Create access key"**
5. Select **"Command Line Interface (CLI)"**
6. Check the confirmation box
7. Click **"Next"** → **"Create access key"**
8. **IMPORTANT**: Copy both:
   - Access key ID
   - Secret access key
9. Click **"Download .csv file"** (backup)
10. Click **"Done"**

**Security Note**: Never share these keys or commit them to Git!

### 1.4 Configure AWS CLI

Open terminal and run:

```bash
aws configure
```

Enter when prompted:
- **AWS Access Key ID**: [paste your access key]
- **AWS Secret Access Key**: [paste your secret key]
- **Default region name**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

Test configuration:
```bash
aws sts get-caller-identity
```

You should see your account ID and user ARN.

---

## Step 2: Create Amazon Connect Instance

### 2.1 Create Connect Instance

1. In AWS Console, search for **"Amazon Connect"**
2. Click **"Create instance"**
3. **Identity management**: Select **"Store users in Amazon Connect"**
4. Click **"Next"**
5. **Administrator**:
   - First name: Your first name
   - Last name: Your last name
   - Username: `admin`
   - Password: Create a strong password (save it!)
   - Email: Your email
6. Click **"Next"**
7. **Telephony**: Keep defaults (both options checked)
8. Click **"Next"**
9. **Data storage**: Keep defaults
10. Click **"Next"**
11. **Review**: Check all settings
12. Click **"Create instance"**

**Wait 2-3 minutes** for instance creation.

### 2.2 Get Instance Details

1. Click on your instance name
2. Copy and save these values:
   - **Instance ARN**: `arn:aws:connect:us-east-1:123456789012:instance/abc-123-def`
   - **Instance ID**: Extract from ARN (last part after `/instance/`)
   - **Instance URL**: `https://your-instance.my.connect.aws`

Example:
```
Instance ARN: arn:aws:connect:us-east-1:994911658700:instance/6091de37-993e-45c8-9637-e9e3a0af5b23
Instance ID: 6091de37-993e-45c8-9637-e9e3a0af5b23
Instance URL: https://unt-sample-cicd-instance-sab-test.my.connect.aws
```

### 2.3 Create Test Agents

1. Click **"Access URL"** to open Connect admin panel
2. Log in with admin credentials
3. Go to **"Users"** → **"User management"**
4. Click **"Add new users"**
5. Create 2 test agents:
   - **Agent 1**:
     - First name: `Test`
     - Last name: `Agent1`
     - Login name: `Agent1`
     - Password: Create password
     - Routing profile: `Basic Routing Profile`
     - Security profile: `Agent`
   - **Agent 2**:
     - First name: `Test`
     - Last name: `Agent2`
     - Login name: `Agent2`
     - Password: Create password
     - Routing profile: `Basic Routing Profile`
     - Security profile: `Agent`
6. Click **"Save"**

### 2.4 Create Test Queue

1. Go to **"Routing"** → **"Queues"**
2. Click **"Add new queue"**
3. Enter:
   - Name: `TestQueue`
   - Description: `Test queue for monitoring app`
4. Click **"Add new queue"**

### 2.5 Assign Queue to Routing Profile

1. Go to **"Users"** → **"Routing profiles"**
2. Click **"Basic Routing Profile"**
3. Under **"Queues"**, click **"Add queue"**
4. Select **"TestQueue"**
5. Set priority: `1`
6. Click **"Save"**

---

## Step 3: Configure IAM Permissions

### 3.1 Create IAM Policy for Connect Access

1. Go to **IAM Console** → **"Policies"**
2. Click **"Create policy"**
3. Click **"JSON"** tab
4. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:SearchUsers",
        "connect:DescribeRoutingProfile",
        "connect:GetCurrentMetricData",
        "connect:GetMetricDataV2",
        "connect:ListQueues",
        "connect:DescribeQueue"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Click **"Next"**
6. Enter policy name: `ConnectQueueMonitorPolicy`
7. Enter description: `Permissions for Connect Queue Monitor app`
8. Click **"Create policy"**

### 3.2 Create IAM Role for Elastic Beanstalk

1. Go to **IAM Console** → **"Roles"**
2. Click **"Create role"**
3. Select **"AWS service"**
4. Select **"EC2"** (Elastic Beanstalk uses EC2)
5. Click **"Next"**
6. Search and select these policies:
   - `AWSElasticBeanstalkWebTier`
   - `AWSElasticBeanstalkWorkerTier`
   - `AWSElasticBeanstalkMulticontainerDocker`
   - `ConnectQueueMonitorPolicy` (the one you just created)
7. Click **"Next"**
8. Enter role name: `aws-elasticbeanstalk-ec2-role`
9. Click **"Create role"**

---

## Step 4: Set Up Local Development Environment

### 4.1 Clone Repository

```bash
# Navigate to your projects folder
cd ~/Documents/Projects  # or your preferred location

# Clone the repository
git clone https://github.com/Sabiha-git-hub/connect-queue-monitor.git

# Navigate into the project
cd connect-queue-monitor
```

### 4.2 Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 4.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- boto3 (AWS SDK)
- Flask-CORS (cross-origin requests)
- python-dotenv (environment variables)
- gunicorn (production server)
- pytz (timezone handling)

---

## Step 5: Configure Application

### 5.1 Create Environment File

```bash
# Copy example environment file
cp .env.example .env
```

### 5.2 Edit Environment File

Open `.env` in a text editor and fill in your values:

```bash
# AWS Configuration
AWS_REGION=us-east-1                    # Your AWS region
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE  # Your access key
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY  # Your secret key

# Amazon Connect Configuration
CONNECT_INSTANCE_ID=6091de37-993e-45c8-9637-e9e3a0af5b23  # Your instance ID
CONNECT_INSTANCE_URL=https://your-instance.my.connect.aws  # Your instance URL

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
PORT=8080  # Local development port
```

### 5.3 Generate Flask Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as `FLASK_SECRET_KEY` in `.env`.

---

## Step 6: Test Locally

### 6.1 Run Application

```bash
python3 run.py
```

You should see:
```
 * Running on http://0.0.0.0:8080
```

### 6.2 Test in Browser

1. Open browser: `http://localhost:8080`
2. You should see the login page
3. Enter username: `Agent1`
4. Click **"Login"**
5. You should see the queue dashboard

### 6.3 Verify Metrics

- Check that queues are displayed
- Verify metrics show values (may be 0 if no activity)
- Wait 15 seconds and verify auto-refresh works

### 6.4 Stop Application

Press `Ctrl+C` in terminal to stop the app.

---

## Step 7: Deploy to Elastic Beanstalk

### 7.1 Initialize Elastic Beanstalk

```bash
# Make sure you're in the project root
cd connect-queue-monitor

# Initialize Elastic Beanstalk
eb init
```

Answer the prompts:
- **Select a default region**: Choose your region (e.g., `us-east-1`)
- **Select an application**: Choose **"Create new Application"**
- **Application name**: `connect-queue-monitor`
- **Platform**: Select **"Python"**
- **Platform branch**: Select **"Python 3.11"** (or latest)
- **CodeCommit**: `n` (no)
- **SSH**: `n` (no, not needed)

### 7.2 Create Environment

```bash
eb create connect-queue-monitor-env
```

This will:
- Create EC2 instance
- Create load balancer
- Set up security groups
- Deploy your application

**Wait 5-10 minutes** for environment creation.

### 7.3 Set Environment Variables

```bash
eb setenv \
  AWS_REGION=us-east-1 \
  CONNECT_INSTANCE_ID=your-instance-id \
  CONNECT_INSTANCE_URL=https://your-instance.my.connect.aws \
  FLASK_SECRET_KEY=your-secret-key \
  AWS_ACCESS_KEY_ID=your-access-key \
  AWS_SECRET_ACCESS_KEY=your-secret-key
```

Replace with your actual values.

### 7.4 Verify Deployment

```bash
# Check environment status
eb status

# Open application in browser
eb open
```

You should see the login page at the Elastic Beanstalk URL.

### 7.5 Get Elastic Beanstalk URL

```bash
eb status | grep CNAME
```

Example output:
```
CNAME: connect-queue-monitor-env.eba-abc123.us-east-1.elasticbeanstalk.com
```

Save this URL - you'll need it for CloudFront.

---

## Step 8: Set Up CloudFront for HTTPS

### 8.1 Create CloudFront Distribution

1. Go to **CloudFront Console**
2. Click **"Create distribution"**
3. **Origin settings**:
   - **Origin domain**: Paste your Elastic Beanstalk URL (without `http://`)
   - **Protocol**: `HTTP only`
   - **HTTP port**: `80`
   - Keep other defaults
4. **Default cache behavior**:
   - **Viewer protocol policy**: `Redirect HTTP to HTTPS`
   - **Allowed HTTP methods**: `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`
   - **Cache policy**: Select **"CachingDisabled"**
   - **Origin request policy**: Select **"AllViewer"**
5. **Settings**:
   - **Price class**: `Use all edge locations` (or choose based on your needs)
   - **Alternate domain name (CNAME)**: Leave empty (or add custom domain if you have one)
6. Click **"Create distribution"**

**Wait 10-15 minutes** for distribution deployment.

### 8.2 Get CloudFront URL

1. Click on your distribution
2. Copy **"Distribution domain name"**
   - Example: `d1234abcd5678.cloudfront.net`
3. Your HTTPS URL: `https://d1234abcd5678.cloudfront.net`

### 8.3 Test CloudFront URL

1. Open browser: `https://your-cloudfront-url`
2. Test login with `Agent1`
3. Verify dashboard loads

---

## Step 9: Add to Amazon Connect

### 9.1 Configure Third-Party Application

1. Open Amazon Connect admin panel
2. Go to **"Routing"** → **"Third-party applications"**
3. Click **"Add application"**
4. Enter:
   - **Application name**: `Queue Monitor`
   - **Application URL**: `https://your-cloudfront-url` (CloudFront URL)
   - **Description**: `Real-time queue monitoring dashboard`
   - **Contact scope**: Select **"Cross contacts"** (important!)
5. Click **"Add application"**

### 9.2 Test in Agent Workspace

1. Open Amazon Connect agent workspace: `https://your-instance.my.connect.aws/agent-app-v2/`
2. Log in as `Agent1`
3. Click **"Third-party applications"** icon in left sidebar
4. You should see **"Queue Monitor"** in the list
5. Click on it - the app should load in the sidebar
6. Verify:
   - App loads without login (auto-detects agent)
   - Queues are displayed
   - Metrics show values
   - Auto-refresh works every 15 seconds

---

## Step 10: Test End-to-End

### 10.1 Test Standalone Mode

1. Open CloudFront URL in new browser tab: `https://your-cloudfront-url`
2. Login with `Agent1`
3. Verify dashboard loads
4. Check metrics update every 15 seconds

### 10.2 Test Embedded Mode

1. Open Amazon Connect agent workspace
2. Log in as `Agent1`
3. Open **"Queue Monitor"** from third-party apps
4. Verify app loads without manual login
5. Verify metrics display correctly

### 10.3 Test Multiple Agents

1. Open incognito/private window
2. Login to agent workspace as `Agent2`
3. Open **"Queue Monitor"**
4. Verify both agents see their respective queues

### 10.4 Test Logout

1. Click **"Logout"** button in the app
2. Verify redirect to login page
3. Login again to verify session works

---

## Troubleshooting

### Issue: "Invalid username" on login

**Cause**: Agent doesn't exist in Amazon Connect

**Solution**:
1. Go to Amazon Connect admin panel
2. Users → User management
3. Verify agent username exists
4. Check spelling (case-sensitive)

### Issue: "No queues assigned"

**Cause**: Agent's routing profile has no queues

**Solution**:
1. Go to Amazon Connect admin panel
2. Users → Routing profiles
3. Click on agent's routing profile
4. Add queues under "Queues" section

### Issue: Metrics show zero

**Cause**: No activity in queues yet

**Solution**:
1. Make a test call to the queue
2. Wait 15 minutes for historical metrics to update
3. Real-time metrics (contacts in queue, available agents) update immediately

### Issue: App doesn't load in Amazon Connect

**Cause**: CSP or CORS configuration issue

**Solution**:
1. Check browser console for errors (F12)
2. Verify CloudFront URL is correct in third-party app settings
3. Verify "Contact scope" is set to "Cross contacts"
4. Check that app is using HTTPS (not HTTP)

### Issue: Session expires immediately

**Cause**: Cookie configuration issue

**Solution**:
1. Verify `FLASK_SECRET_KEY` is set in Elastic Beanstalk environment
2. Check that CloudFront is using HTTPS
3. Clear browser cookies and try again

### Issue: Elastic Beanstalk deployment fails

**Cause**: Missing dependencies or configuration

**Solution**:
1. Check logs: `eb logs`
2. Verify all environment variables are set: `eb printenv`
3. Verify IAM role has correct permissions
4. Redeploy: `eb deploy`

### Issue: High AWS costs

**Cause**: Unexpected resource usage

**Solution**:
1. Check AWS Cost Explorer
2. Verify only one Elastic Beanstalk environment is running
3. Consider reducing refresh interval from 15s to 30s
4. Review `docs/COST_ANALYSIS.md` for optimization tips

---

## Post-Deployment Checklist

- [ ] Application loads at CloudFront URL
- [ ] Login works with test agents
- [ ] Queues are displayed correctly
- [ ] Metrics update every 15 seconds
- [ ] App works in Amazon Connect agent workspace
- [ ] Auto-detection works in embedded mode
- [ ] Logout works correctly
- [ ] Multiple agents can use simultaneously
- [ ] Branding (logo) displays correctly
- [ ] Performance summary shows correct data

---

## Next Steps

### Customize Branding

1. Replace logo: `app/static/images/logo.png`
2. Update colors in: `app/static/css/styles.css`
3. Redeploy: `eb deploy`
4. Invalidate CloudFront cache (if frontend changed):
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id YOUR-DISTRIBUTION-ID \
     --paths "/*"
   ```

### Add More Agents

1. Go to Amazon Connect admin panel
2. Users → User management
3. Add new users with "Agent" security profile
4. Assign to routing profile with queues

### Monitor Costs

1. Set up AWS Budget:
   - Go to AWS Billing Console
   - Create budget for $50/month
   - Set up email alerts
2. Review costs weekly in Cost Explorer

### Set Up Monitoring

1. Go to CloudWatch Console
2. Create alarms for:
   - Elastic Beanstalk health
   - High error rates
   - High latency
3. Set up SNS notifications

---

## Cost Estimate

For 50 agents with 15-second refresh:

| Service | Monthly Cost |
|---------|--------------|
| Elastic Beanstalk (t3.micro) | $8.50 |
| Application Load Balancer | $8.00 |
| CloudFront | $1.00 |
| Amazon Connect API calls | $19.00 |
| Data transfer | $0.50 |
| **Total** | **~$37/month** |

See `docs/COST_ANALYSIS.md` for detailed breakdown.

---

## Support

- **Documentation**: Check `docs/` folder
- **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **API Reference**: See `docs/API_REFERENCE.md`
- **GitHub Issues**: https://github.com/Sabiha-git-hub/connect-queue-monitor/issues

---

## Summary

You've successfully deployed the Connect Queue Monitor! 🎉

**What you built**:
- Flask application on Elastic Beanstalk
- HTTPS access via CloudFront
- Integration with Amazon Connect
- Real-time queue monitoring
- Personal performance dashboard
- Auto-refresh every 15 seconds

**URLs to save**:
- Elastic Beanstalk: `http://your-env.elasticbeanstalk.com`
- CloudFront (HTTPS): `https://your-distribution.cloudfront.net`
- Amazon Connect: `https://your-instance.my.connect.aws`

**Next demo**: Ready in 23 days! 🚀
