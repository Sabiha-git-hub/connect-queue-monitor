# AWS App Runner Deployment Guide

This guide walks you through deploying your Amazon Connect Queue Monitor app to AWS App Runner.

## Why App Runner?

AWS App Runner is designed specifically for containerized web applications and APIs. Unlike Amplify (which is for static sites), App Runner:
- Runs your Flask server continuously
- Automatically scales based on traffic
- Handles HTTPS certificates automatically
- Provides a permanent URL
- Costs approximately $5-10/month for low traffic

## Prerequisites

- AWS Account with access to App Runner
- GitHub repository: https://github.com/Sabiha-git-hub/connect-queue-monitor
- Your AWS credentials (for environment variables)

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

The required files are already in your repository:
- `apprunner.yaml` - App Runner configuration
- `requirements.txt` - Python dependencies
- `Procfile` - Gunicorn configuration
- All your Flask app code

### Step 2: Push Latest Changes to GitHub

```bash
git add apprunner.yaml
git commit -m "Add App Runner configuration"
git push origin main
```

### Step 3: Create App Runner Service

1. **Open AWS Console**
   - Go to https://console.aws.amazon.com
   - Search for "App Runner" in the search bar
   - Click on "AWS App Runner"

2. **Create Service**
   - Click "Create service" button
   - Select "Source code repository"

3. **Connect to GitHub**
   - Click "Add new" under "Source code repository"
   - Select "GitHub"
   - Click "Connect to GitHub" and authorize AWS
   - Select your repository: `Sabiha-git-hub/connect-queue-monitor`
   - Branch: `main`
   - Click "Next"

4. **Configure Build**
   - Deployment trigger: "Automatic" (deploys on every push)
   - Build settings: "Use a configuration file"
   - Configuration file: `apprunner.yaml`
   - Click "Next"

5. **Configure Service**
   - Service name: `connect-queue-monitor`
   - Virtual CPU: 1 vCPU
   - Memory: 2 GB
   - Port: 8080 (should auto-fill from apprunner.yaml)

6. **Add Environment Variables**
   Click "Add environment variable" for each of these:

   **IMPORTANT: Use regular AWS_* prefix (not CONNECT_AWS_*)**
   
   ```
   AWS_REGION = us-east-1
   AWS_ACCESS_KEY_ID = <your-access-key-from-.env>
   AWS_SECRET_ACCESS_KEY = <your-secret-key-from-.env>
   AWS_SESSION_TOKEN = <your-session-token-from-.env>
   CONNECT_INSTANCE_ID = 6091de37-993e-45c8-9637-e9e3a0af5b23
   CONNECT_INSTANCE_URL = https://unt-sample-cicd-instance-sab-test.my.connect.aws
   FLASK_SECRET_KEY = 72822dc31892eac04d7d01afc2fa0ef5826f8d0ee01a43574d4995f6952c43a2
   FLASK_DEBUG = False
   ALLOWED_ORIGINS = https://unt-sample-cicd-instance-sab-test.my.connect.aws,https://unt-sample-cicd-instance-sab-test.awsapps.com
   ```

7. **Configure Auto Scaling (Optional)**
   - Min instances: 1
   - Max instances: 2
   - Max concurrency: 100

8. **Configure Health Check**
   - Protocol: HTTP
   - Path: `/`
   - Interval: 10 seconds
   - Timeout: 5 seconds
   - Healthy threshold: 1
   - Unhealthy threshold: 5

9. **Security**
   - Leave default settings (App Runner creates a service role automatically)

10. **Review and Create**
    - Review all settings
    - Click "Create & deploy"

### Step 4: Wait for Deployment

- Deployment takes 5-10 minutes
- You'll see status: "Operation in progress"
- Wait until status shows: "Running"

### Step 5: Get Your App URL

Once deployed, you'll see:
- **Default domain**: Something like `https://abc123xyz.us-east-1.awsapprunner.com`
- This is your permanent URL!

### Step 6: Test Your App

1. Open the App Runner URL in your browser
2. You should see the login page
3. Test login with your Connect credentials

### Step 7: Update Amazon Connect Third-Party App

1. Go to Amazon Connect console
2. Navigate to: Admin → Third-party applications
3. Find your "Queue Monitor" app
4. Update the configuration:
   - **Application URL**: `https://your-app-runner-url.awsapprunner.com`
   - **Allowed origins**: Add `https://your-app-runner-url.awsapprunner.com`
5. Save changes

### Step 8: Test in Amazon Connect

1. Log into Amazon Connect as an agent
2. Open the agent workspace
3. Your Queue Monitor app should appear in the third-party apps section
4. Click to open it - should work without login page (automatic detection via Streams API)

## Monitoring and Logs

### View Logs
1. In App Runner console, click on your service
2. Go to "Logs" tab
3. Click "View in CloudWatch"
4. You can see all application logs here

### View Metrics
1. In App Runner console, click on your service
2. Go to "Metrics" tab
3. See requests, response times, CPU, memory usage

## Updating Your App

Whenever you push changes to GitHub:
1. `git add .`
2. `git commit -m "Your changes"`
3. `git push origin main`
4. App Runner automatically detects the push and redeploys (takes 5-10 minutes)

## Troubleshooting

### Deployment Failed
- Check the "Logs" tab in App Runner console
- Look for error messages in the build or deployment logs
- Common issues:
  - Missing environment variables
  - Syntax errors in apprunner.yaml
  - Missing dependencies in requirements.txt

### App Returns 500 Error
- Check CloudWatch logs for Python errors
- Verify all environment variables are set correctly
- Check that AWS credentials are valid

### App Not Loading in Amazon Connect
- Verify ALLOWED_ORIGINS includes both Connect URLs
- Check that Application URL in Connect matches App Runner URL
- Verify CORS headers are working (check browser console)

### AWS Credentials Expired
Your temporary credentials will expire. When they do:
1. Get new credentials from AWS
2. Update environment variables in App Runner:
   - Go to App Runner console
   - Click your service
   - Go to "Configuration" tab
   - Click "Edit" under "Environment variables"
   - Update AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
   - Click "Save changes"
   - App Runner will automatically redeploy with new credentials

## Cost Estimate

App Runner pricing (us-east-1):
- **Provisioned container**: $0.007/hour = ~$5/month
- **vCPU**: $0.064 per vCPU-hour (only when processing requests)
- **Memory**: $0.007 per GB-hour (only when processing requests)

For low traffic (demo/workshop):
- Estimated cost: $5-10/month
- Much cheaper than running EC2 instances 24/7

## Deleting the Service

If you want to delete the service later:
1. Go to App Runner console
2. Select your service
3. Click "Actions" → "Delete service"
4. Confirm deletion
5. This stops all charges

## Comparison: App Runner vs Amplify

| Feature | App Runner | Amplify |
|---------|-----------|---------|
| **Best for** | Web servers, APIs | Static sites, SPAs |
| **Python Flask** | ✅ Yes | ❌ No |
| **Continuous server** | ✅ Yes | ❌ No |
| **Auto-scaling** | ✅ Yes | ✅ Yes |
| **HTTPS** | ✅ Automatic | ✅ Automatic |
| **Cost** | ~$5-10/month | ~$1-5/month |
| **Setup complexity** | Medium | Easy |

## Next Steps

After successful deployment:
1. Test thoroughly in Amazon Connect agent workspace
2. Share the App Runner URL with your demo audience
3. Monitor logs and metrics before demo day
4. Consider setting up CloudWatch alarms for errors

## Support

If you encounter issues:
1. Check CloudWatch logs first
2. Verify environment variables
3. Test the URL directly in browser
4. Check Amazon Connect third-party app configuration
