# Quick Deployment Checklist

Use this checklist when deploying to a new AWS account/Connect instance. For detailed instructions, see `DEPLOYMENT_FROM_SCRATCH.md`.

## Pre-Deployment (30 minutes)

- [ ] AWS account created
- [ ] IAM user created with access keys
- [ ] AWS CLI configured (`aws configure`)
- [ ] EB CLI installed (`pip install awsebcli`)
- [ ] Python 3.11+ installed
- [ ] Git installed

## Amazon Connect Setup (30 minutes)

- [ ] Connect instance created
- [ ] Instance ID copied: `________________`
- [ ] Instance URL copied: `________________`
- [ ] Admin user created
- [ ] 2+ test agents created (usernames: `________________`)
- [ ] Test queue created
- [ ] Queue assigned to routing profile

## IAM Configuration (15 minutes)

- [ ] IAM policy created: `ConnectQueueMonitorPolicy`
- [ ] IAM role created: `aws-elasticbeanstalk-ec2-role`
- [ ] Policies attached to role:
  - [ ] `AWSElasticBeanstalkWebTier`
  - [ ] `ConnectQueueMonitorPolicy`

## Local Setup (15 minutes)

- [ ] Repository cloned
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created from `.env.example`
- [ ] Environment variables filled in `.env`:
  - [ ] `AWS_REGION`
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
  - [ ] `CONNECT_INSTANCE_ID`
  - [ ] `CONNECT_INSTANCE_URL`
  - [ ] `FLASK_SECRET_KEY` (generated)

## Local Testing (10 minutes)

- [ ] App runs locally (`python3 run.py`)
- [ ] Login page loads at `http://localhost:8080`
- [ ] Login works with test agent
- [ ] Dashboard displays queues
- [ ] Metrics show values
- [ ] Auto-refresh works (15 seconds)

## Elastic Beanstalk Deployment (30 minutes)

- [ ] EB initialized (`eb init`)
- [ ] Environment created (`eb create connect-queue-monitor-env`)
- [ ] Environment variables set (`eb setenv ...`)
- [ ] Deployment successful (`eb status` shows "Green")
- [ ] EB URL copied: `________________`
- [ ] App accessible at EB URL

## CloudFront Setup (20 minutes)

- [ ] CloudFront distribution created
- [ ] Origin set to Elastic Beanstalk URL
- [ ] Cache policy: `CachingDisabled`
- [ ] Origin request policy: `AllViewer`
- [ ] Distribution deployed (wait 10-15 min)
- [ ] CloudFront URL copied: `________________`
- [ ] HTTPS URL works: `https://________________`

## Amazon Connect Integration (10 minutes)

- [ ] Third-party app added in Connect admin
- [ ] App name: `Queue Monitor`
- [ ] App URL: CloudFront HTTPS URL
- [ ] Contact scope: `Cross contacts`
- [ ] App visible in agent workspace
- [ ] App loads in sidebar

## End-to-End Testing (15 minutes)

- [ ] Standalone mode works (CloudFront URL)
- [ ] Login works
- [ ] Dashboard loads
- [ ] Metrics display
- [ ] Auto-refresh works
- [ ] Embedded mode works (Connect agent workspace)
- [ ] Auto-detection works (no manual login)
- [ ] Multiple agents can use simultaneously
- [ ] Logout works
- [ ] Branding (logo) displays

## Post-Deployment (10 minutes)

- [ ] URLs documented:
  - EB URL: `________________`
  - CloudFront URL: `________________`
  - Connect URL: `________________`
- [ ] Access keys stored securely
- [ ] AWS budget alert set up ($50/month)
- [ ] CloudWatch alarms configured (optional)
- [ ] Documentation reviewed

## Total Time: ~3 hours

---

## Quick Commands Reference

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Run locally
python3 run.py

# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Elastic Beanstalk
```bash
# Initialize
eb init

# Create environment
eb create connect-queue-monitor-env

# Set environment variables
eb setenv AWS_REGION=us-east-1 CONNECT_INSTANCE_ID=xxx ...

# Check status
eb status

# View logs
eb logs

# Deploy changes
eb deploy

# Open in browser
eb open

# Terminate environment (cleanup)
eb terminate connect-queue-monitor-env
```

### CloudFront
```bash
# Invalidate cache (after frontend changes)
aws cloudfront create-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --paths "/*"
```

### Git
```bash
# Clone repository
git clone https://github.com/Sabiha-git-hub/connect-queue-monitor.git

# Pull latest changes
git pull origin main
```

---

## Troubleshooting Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| "Invalid username" | Check agent exists in Connect admin |
| "No queues assigned" | Add queues to routing profile |
| Metrics show zero | Wait 15 min for historical data |
| App doesn't load in Connect | Check Contact scope = "Cross contacts" |
| Session expires immediately | Verify FLASK_SECRET_KEY is set |
| EB deployment fails | Check logs: `eb logs` |
| High costs | Review Cost Explorer, reduce refresh interval |

---

## Important URLs

- **AWS Console**: https://console.aws.amazon.com
- **GitHub Repository**: https://github.com/Sabiha-git-hub/connect-queue-monitor
- **Documentation**: See `docs/` folder
- **Detailed Guide**: `DEPLOYMENT_FROM_SCRATCH.md`

---

## Cost Estimate

**~$37/month** for 50 agents with 15-second refresh

Breakdown:
- Elastic Beanstalk: $17/month
- CloudFront: $1/month
- Connect API calls: $19/month

See `docs/COST_ANALYSIS.md` for details.

---

## Support

- Detailed guide: `DEPLOYMENT_FROM_SCRATCH.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Architecture: `docs/ARCHITECTURE.md`
- API reference: `docs/API_REFERENCE.md`
