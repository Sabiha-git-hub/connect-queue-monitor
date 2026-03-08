# Setting Up as Amazon Connect Third-Party Application

## 📋 Prerequisites

Before you can register your app as a third-party application in Amazon Connect, you need:

1. ✅ A publicly accessible URL (HTTPS required)
2. ✅ Your app deployed to a server
3. ✅ Proper CORS configuration
4. ✅ Amazon Connect instance admin access

---

## 🌐 Step 1: Deploy Your App

### Option A: Quick Test with ngrok (For Testing Only)

**ngrok** creates a temporary public URL for your local app:

1. **Install ngrok**:
   ```bash
   brew install ngrok
   ```

2. **Create ngrok account and get authtoken**:
   - Go to: https://dashboard.ngrok.com/signup
   - Sign up for a free account
   - Copy your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken

3. **Configure ngrok with your authtoken**:
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
   ```

4. **Start your Flask app** (in one terminal):
   ```bash
   source venv/bin/activate
   python3 run.py
   ```

5. **Start ngrok** (in another terminal):
   ```bash
   ngrok http 8080
   ```

6. **Copy the HTTPS URL** from ngrok output:
   ```
   Forwarding: https://incisural-fantastically-ruby.ngrok-free.dev -> http://localhost:8080
   ```
   
   Your app URL will be something like: `https://your-subdomain.ngrok-free.dev`

7. **Important**: When visitors first access your ngrok URL, they'll see a warning page. Click "Visit Site" to continue.

⚠️ **Note**: 
- Free ngrok URLs change every time you restart ngrok
- You'll need to update the third-party app URL in Amazon Connect each time
- For permanent URLs, upgrade to ngrok paid plan or deploy to AWS

### Option B: Deploy to AWS (Recommended for Production)

#### Using AWS Elastic Beanstalk

1. **Install EB CLI**:
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB**:
   ```bash
   eb init -p python-3.9 connect-queue-monitor
   ```

3. **Create environment**:
   ```bash
   eb create connect-queue-monitor-env
   ```

4. **Deploy**:
   ```bash
   eb deploy
   ```

5. **Get your URL**:
   ```bash
   eb status
   ```
   
   Your app URL will be: `https://connect-queue-monitor-env.us-east-1.elasticbeanstalk.com`

#### Using AWS EC2

1. Launch an EC2 instance (Amazon Linux 2 or Ubuntu)
2. Install Python and dependencies
3. Set up Nginx as reverse proxy
4. Configure SSL certificate (use AWS Certificate Manager)
5. Run app with Gunicorn

---

## 🔧 Step 2: Update Your App Configuration

Once you have a public URL, update your `.env` file:

```bash
# Change this from localhost to your public domain
CONNECT_INSTANCE_URL=https://unt-sample-cicd-instance-sab-test.my.connect.aws

# Add your public app URL to allowed origins
ALLOWED_ORIGINS=https://unt-sample-cicd-instance-sab-test.my.connect.aws,https://unt-sample-cicd-instance-sab-test.awsapps.com

# Disable debug mode for production
FLASK_DEBUG=False
```

---

## 🎯 Step 3: Register in Amazon Connect Console

### Navigate to Third-Party Applications

1. **Open Amazon Connect Console**: https://console.aws.amazon.com/connect/
2. **Select your instance**: Click on your instance alias (e.g., `unt-sample-cicd-instance-sab-test`)
3. **In the left navigation menu**: 
   - Scroll down to the "Channels" section
   - Click **"Agent applications"**
4. **Click**: "Add application" button (top right)

### Fill in Application Details

#### Basic Information
- **Application name**: `Queue Monitor` (or any name you prefer - this is what agents will see)
- **Application URL**: Your ngrok or deployed app URL
  - Example: `https://incisural-fantastically-ruby.ngrok-free.dev`
  - Must be HTTPS (not HTTP)
- **Description** (optional): `Real-time queue monitoring - displays assigned queues and call counts`

#### Security Settings (After Creating)

After you create the application, you need to configure security:

1. **Click on your newly created application** in the list
2. **Under "Security" section**, add to **Allowed origins**:
   - Your ngrok URL: `https://incisular-fantastically-ruby.ngrok-free.dev`
   - Your Connect instance URL: `https://unt-sample-cicd-instance-sab-test.my.connect.aws`
   - Your Connect awsapps URL: `https://unt-sample-cicd-instance-sab-test.awsapps.com`
3. **Click "Save"**

#### Access Control (Optional)

You can control who sees the app:
- **All agents** (default) - Everyone can see it
- **Specific security profiles** - Only agents with certain permissions
- **Specific routing profiles** - Only agents in certain routing profiles

---

## 🔐 Step 4: Configure CORS and Security

Your app is already configured for CORS, but verify these settings:

### In `app/__init__.py`

The app automatically configures CORS based on your `.env` file:

```python
# CORS is configured to allow:
# 1. Your Connect instance URL
# 2. Your Connect awsapps URL
# 3. In development: localhost origins
```

### Required Headers (Already Configured)

Your app already sends these headers:
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Credentials`
- `Content-Security-Policy`
- `X-Frame-Options: ALLOWALL` (allows iframe embedding)

---

## 📱 Step 5: Test the Integration

### In Amazon Connect Agent Workspace

1. **Login as an agent** to your Connect instance
2. **Look for your app** in the agent workspace sidebar
3. **Click on "Queue Monitor"**
4. **Verify**:
   - App loads in iframe
   - Streams API detects agent automatically
   - No login form appears (automatic detection)
   - Queues and call counts display correctly

### Troubleshooting Embedded Mode

If the app shows a login form when embedded:

1. **Check browser console** for errors
2. **Verify Streams API** is loading:
   ```javascript
   // Should see in console:
   "Streams API loaded successfully"
   "Embedded mode detected"
   ```

3. **Check CORS errors**:
   - Make sure your app URL is in `ALLOWED_ORIGINS`
   - Verify Connect instance URL matches exactly

---

## 🔍 What to Put in Each Field

### Amazon Connect Console Fields

| Field | What to Enter | Example |
|-------|---------------|---------|
| **Application URL** | Your deployed app's public HTTPS URL | `https://incisural-fantastically-ruby.ngrok-free.dev` |
| **Application name** | Display name agents will see | `Queue Monitor` |
| **Description** | What the app does (optional) | `View assigned queues and call counts` |
| **Allowed origins** | URLs that can embed your app | Your ngrok URL, Connect instance URL, Connect awsapps URL |

### Your .env File

| Variable | What to Enter | Example |
|----------|---------------|---------|
| **CONNECT_INSTANCE_ID** | Your Connect instance UUID | `6091de37-993e-45c8-9637-e9e3a0af5b23` |
| **CONNECT_INSTANCE_URL** | Your Connect instance URL | `https://unt-sample-cicd-instance-sab-test.my.connect.aws` |
| **ALLOWED_ORIGINS** | Comma-separated list of allowed domains | `https://unt-sample-cicd-instance-sab-test.my.connect.aws,https://unt-sample-cicd-instance-sab-test.awsapps.com` |

---

## 🚀 Quick Setup Checklist

### For Testing with ngrok:

- [ ] Install ngrok: `brew install ngrok`
- [ ] Create ngrok account at https://dashboard.ngrok.com/signup
- [ ] Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
- [ ] Configure ngrok: `ngrok config add-authtoken YOUR_AUTHTOKEN`
- [ ] Start Flask app: `source venv/bin/activate && python3 run.py`
- [ ] Start ngrok in another terminal: `ngrok http 8080`
- [ ] Copy the HTTPS URL from ngrok (e.g., `https://your-subdomain.ngrok-free.dev`)
- [ ] Open Amazon Connect Console: https://console.aws.amazon.com/connect/
- [ ] Select your instance
- [ ] Go to: Channels → Agent applications
- [ ] Click "Add application"
- [ ] Enter application name: `Queue Monitor`
- [ ] Enter application URL: Your ngrok HTTPS URL
- [ ] Click "Add application"
- [ ] Click on your new application to configure security
- [ ] Add to "Allowed origins":
  - [ ] Your ngrok URL
  - [ ] Your Connect instance URL (e.g., `https://unt-sample-cicd-instance-sab-test.my.connect.aws`)
  - [ ] Your Connect awsapps URL (e.g., `https://unt-sample-cicd-instance-sab-test.awsapps.com`)
- [ ] Save security settings
- [ ] Log into Amazon Connect as an agent
- [ ] Look for "Queue Monitor" in the agent workspace applications panel
- [ ] Click to open - should load without login form
- [ ] Verify queues and call counts display correctly

### For Production Deployment:

- [ ] Deploy app to AWS (Elastic Beanstalk, EC2, or other)
- [ ] Get permanent HTTPS URL
- [ ] Update `.env` with production settings
- [ ] Set `FLASK_DEBUG=False`
- [ ] Use IAM roles instead of hardcoded credentials
- [ ] Follow the same Amazon Connect console steps above with your production URL
- [ ] Set up CloudWatch logging
- [ ] Configure monitoring and alerts

---

## 🎨 Customization Options

### Change App Display Name
In Amazon Connect console, you can change the display name agents see.

### Add App Icon
Upload a custom icon in the third-party application settings.

### Control Access
Restrict which agents can see the app based on:
- Security profiles
- Routing profiles
- Agent hierarchy

---

## 📊 Monitoring and Logs

### Check App Logs
```bash
# If using Elastic Beanstalk
eb logs

# If using EC2
tail -f /var/log/your-app.log
```

### Monitor Usage
- Check CloudWatch logs for errors
- Monitor API call counts
- Track agent usage patterns

---

## 🔒 Security Best Practices

### For Production Deployment

1. **Use HTTPS only** - Never use HTTP
2. **Set strong CORS policies** - Only allow your Connect instance
3. **Use IAM roles** - Don't hardcode AWS credentials
4. **Enable CloudWatch logging** - Monitor for issues
5. **Set up alerts** - Get notified of errors
6. **Regular updates** - Keep dependencies updated
7. **Backup configuration** - Save your `.env` settings securely

### Environment Variables for Production

```bash
# Production .env example
AWS_REGION=us-east-1
CONNECT_INSTANCE_ID=6091de37-993e-45c8-9637-e9e3a0af5b23
CONNECT_INSTANCE_URL=https://unt-sample-cicd-instance-sab-test.my.connect.aws
FLASK_SECRET_KEY=<generate-a-strong-random-key>
FLASK_DEBUG=False
ALLOWED_ORIGINS=https://unt-sample-cicd-instance-sab-test.my.connect.aws,https://unt-sample-cicd-instance-sab-test.awsapps.com

# Use IAM role instead of hardcoded credentials
# AWS_ACCESS_KEY_ID=<not-needed-with-iam-role>
# AWS_SECRET_ACCESS_KEY=<not-needed-with-iam-role>
```

---

## 🆘 Common Issues

### Issue: "Application failed to load"
**Solution**: 
- Check that your Flask app is running (`python3 run.py`)
- Check that ngrok is running (`ngrok http 8080`)
- Verify the ngrok URL is correct in Amazon Connect
- Check CORS settings in the application security settings

### Issue: "ngrok warning page appears"
**Solution**: This is normal for free ngrok accounts. Click "Visit Site" to continue. Visitors will need to do this once per session.

### Issue: "Login form appears in embedded mode"
**Solution**: 
- Verify Streams API is loading correctly (check browser console)
- Make sure you're accessing from within Amazon Connect agent workspace
- Check that allowed origins include your Connect instance URLs

### Issue: "Access denied" errors
**Solution**: 
- Check IAM permissions for Connect API access
- Verify AWS credentials in `.env` file
- Make sure credentials have `connect:*` permissions

### Issue: "Queues not displaying" or "All queues show 0 calls"
**Solution**: 
- Verify agent has queues assigned in their routing profile
- Check that calls are actually in queue (verify in Amazon Connect real-time metrics)
- Refresh the page or click the refresh button
- Check Flask logs for API errors

### Issue: "ngrok URL changed after restart"
**Solution**: 
- Free ngrok URLs change each time you restart
- Update the application URL in Amazon Connect console
- Update allowed origins in security settings
- Consider ngrok paid plan for permanent URLs

### Issue: "ERR_NGROK_8012 - Connection refused"
**Solution**: 
- Make sure Flask app is running before starting ngrok
- Verify Flask is running on port 8080
- Check that virtual environment is activated: `source venv/bin/activate`

---

## 📚 Additional Resources

- [Amazon Connect Third-Party Applications Guide](https://docs.aws.amazon.com/connect/latest/adminguide/3p-apps.html)
- [Amazon Connect Streams API Documentation](https://github.com/amazon-connect/amazon-connect-streams)
- [AWS Elastic Beanstalk Python Guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-apps.html)

---

**Ready to deploy?** Start with ngrok for quick testing, then move to AWS for production! 🚀
