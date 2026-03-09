# Troubleshooting Guide

Common issues and solutions for the Connect Queue Monitor application.

## Table of Contents
- [Login Issues](#login-issues)
- [Session Issues](#session-issues)
- [Metrics Issues](#metrics-issues)
- [Embedding Issues](#embedding-issues)
- [Deployment Issues](#deployment-issues)
- [AWS API Issues](#aws-api-issues)
- [Performance Issues](#performance-issues)

---

## Login Issues

### Issue: "Invalid username" error

**Symptoms**: Login form shows error message after entering username

**Possible Causes**:
1. Username doesn't exist in Amazon Connect
2. Username spelling is incorrect
3. AWS credentials are invalid or expired
4. Connect instance ID is incorrect

**Solutions**:

1. **Verify username exists**:
   - Log into Amazon Connect admin panel
   - Go to Users → User management
   - Search for the username
   - Ensure username matches exactly (case-sensitive)

2. **Check AWS credentials**:
   ```bash
   # Test AWS credentials
   aws sts get-caller-identity
   
   # Should return your account ID
   ```

3. **Verify environment variables**:
   ```bash
   # Check Elastic Beanstalk environment
   eb printenv
   
   # Should show:
   # AWS_REGION = us-east-1
   # CONNECT_INSTANCE_ID = 6091de37-993e-45c8-9637-e9e3a0af5b23
   # CONNECT_INSTANCE_URL = https://unt-sample-cicd-instance-sab-test.my.connect.aws
   ```

4. **Check CloudWatch logs**:
   - Go to CloudWatch → Log groups
   - Find `/aws/elasticbeanstalk/connect-queue-monitor-env/var/log/web.stdout.log`
   - Look for error messages related to SearchUsers API call

---

### Issue: Login page doesn't load

**Symptoms**: Blank page or "502 Bad Gateway" error

**Possible Causes**:
1. Elastic Beanstalk environment is not running
2. CloudFront distribution is not deployed
3. DNS issues

**Solutions**:

1. **Check Elastic Beanstalk status**:
   ```bash
   eb status
   
   # Should show: Health: Green
   ```

2. **Check CloudFront distribution**:
   - Go to CloudFront console
   - Find distribution `E2ZQ9PY5KN8UMB`
   - Status should be "Deployed"
   - State should be "Enabled"

3. **Test direct Elastic Beanstalk URL**:
   ```bash
   curl http://connect-queue-monitor-env.eba-iuzmyq3n.us-east-1.elasticbeanstalk.com
   
   # Should return HTML
   ```

4. **Check application logs**:
   ```bash
   eb logs
   ```

---

## Session Issues

### Issue: Session expires immediately after login

**Symptoms**: Redirected to login page right after successful login

**Possible Causes**:
1. Session cookie not being set correctly
2. Cookie domain mismatch
3. Browser blocking third-party cookies

**Solutions**:

1. **Check cookie settings in browser**:
   - Open DevTools (F12)
   - Go to Application → Cookies
   - Look for `session` cookie
   - Verify attributes: `HttpOnly`, `Secure`, `SameSite=None`

2. **Verify session configuration** in `app/__init__.py`:
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   app.config['SESSION_COOKIE_SAMESITE'] = 'None'
   app.config['SESSION_COOKIE_PARTITIONED'] = True
   ```

3. **Test in incognito mode**:
   - Open incognito/private window
   - Try logging in
   - If it works, clear browser cookies and try again

4. **Check FLASK_SECRET_KEY**:
   ```bash
   eb printenv | grep FLASK_SECRET_KEY
   
   # Should return a long random string
   ```

---

### Issue: "Not authenticated" error on refresh

**Symptoms**: AJAX refresh returns 401 error

**Possible Causes**:
1. Session expired (24 hours)
2. Session cookie was cleared
3. Server restarted and sessions were lost

**Solutions**:

1. **Log in again**: Sessions expire after 24 hours

2. **Check session storage**: Ensure sessions are persisted
   - For Elastic Beanstalk: Sessions stored in memory (lost on restart)
   - For production: Consider using Redis or DynamoDB for session storage

3. **Increase session lifetime** in `app/__init__.py`:
   ```python
   from datetime import timedelta
   app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=48)  # 48 hours
   ```

---

## Metrics Issues

### Issue: Metrics show zero or blank values

**Symptoms**: Queue table shows 0 for all metrics or blank cells

**Possible Causes**:
1. No activity in queues today
2. Agent not assigned to any queues
3. AWS API permissions issue
4. Timezone mismatch

**Solutions**:

1. **Verify agent has queues assigned**:
   - Log into Amazon Connect admin panel
   - Go to Users → User management
   - Click on agent
   - Check "Routing profile" → Should have queues assigned

2. **Check IAM permissions**:
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
           "connect:GetMetricDataV2"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **Verify timezone configuration** in `app/services/queue_service.py`:
   ```python
   timezone = pytz.timezone('America/New_York')  # EST/EDT
   ```

4. **Test API calls manually**:
   ```bash
   aws connect get-current-metric-data \
     --instance-id 6091de37-993e-45c8-9637-e9e3a0af5b23 \
     --filters '{"Queues":["<queue-arn>"]}' \
     --current-metrics '[{"Name":"CONTACTS_IN_QUEUE","Unit":"COUNT"}]' \
     --region us-east-1
   ```

---

### Issue: Historical metrics not updating

**Symptoms**: "Calls Handled" and "Calls Transferred" show old values

**Possible Causes**:
1. AWS Connect processes historical metrics with delay (5-15 minutes)
2. No new calls have been handled
3. Metric aggregation period is incorrect

**Solutions**:

1. **Wait 15 minutes**: Historical metrics update with delay

2. **Verify calls are being handled**:
   - Log into Amazon Connect agent workspace
   - Handle a test call
   - Wait 15 minutes
   - Refresh the dashboard

3. **Check metric time range** in `app/services/queue_service.py`:
   ```python
   # Should be from midnight to now
   start_time = timezone.localize(datetime.combine(today, datetime.min.time()))
   end_time = timezone.localize(datetime.now())
   ```

4. **Check CloudWatch logs** for GetMetricDataV2 errors

---

### Issue: "CONTACTS_MISSED" metric not available

**Symptoms**: Error message about CONTACTS_MISSED metric

**Cause**: AWS Connect GetMetricDataV2 API does not support CONTACTS_MISSED metric

**Solution**: This is an AWS limitation, not a bug. The metric has been removed from the application. Use "Calls Handled" and "Calls Transferred" instead.

---

### Issue: "Non-Productive" count is incorrect

**Symptoms**: Non-Productive count doesn't match agents in custom status

**Possible Causes**:
1. Using wrong metric (AGENTS_AFTER_CONTACT_WORK instead of AGENTS_NON_PRODUCTIVE)
2. Agent status not configured correctly in Connect

**Solutions**:

1. **Verify metric name** in `app/services/queue_service.py`:
   ```python
   # Correct metric
   {'Name': 'AGENTS_NON_PRODUCTIVE', 'Unit': 'COUNT'}
   
   # Wrong metric (don't use this)
   {'Name': 'AGENTS_AFTER_CONTACT_WORK', 'Unit': 'COUNT'}
   ```

2. **Check agent status configuration**:
   - Log into Amazon Connect admin panel
   - Go to Routing → Agent status
   - Verify custom statuses are configured correctly

---

## Embedding Issues

### Issue: "Content blocked" error in Amazon Connect

**Symptoms**: App doesn't load when embedded in Amazon Connect, shows CSP error

**Possible Causes**:
1. Amazon Connect domains not in allowed origins
2. CSP headers blocking iframe embedding

**Solutions**:

1. **Verify CORS configuration** in `app/__init__.py`:
   ```python
   CORS(app, 
        origins=[
            'https://dzh4oz4t3wz32.cloudfront.net',
            'https://unt-sample-cicd-instance-sab-test.my.connect.aws',
            'https://*.awsapps.com',
            'https://*.my.connect.aws'
        ],
        supports_credentials=True)
   ```

2. **Check CSP headers** in `app/__init__.py`:
   ```python
   @app.after_request
   def add_security_headers(response):
       response.headers['Content-Security-Policy'] = (
           "frame-ancestors 'self' https://*.awsapps.com https://*.my.connect.aws"
       )
       return response
   ```

3. **Verify app configuration in Amazon Connect**:
   - Go to Amazon Connect admin panel
   - Routing → Third-party applications
   - Check URL is correct: `https://dzh4oz4t3wz32.cloudfront.net`
   - Check "Contact scope" is set to "Cross contacts"

---

### Issue: App closes after each call

**Symptoms**: App disappears from agent workspace after call ends

**Cause**: Contact scope set to "Per contact" instead of "Cross contacts"

**Solution**:

1. **Update app configuration in Amazon Connect**:
   - Go to Amazon Connect admin panel
   - Routing → Third-party applications
   - Find "Connect Queue Monitor"
   - Change "Contact scope" to "Cross contacts"
   - Save changes

2. **Refresh agent workspace**: Agents need to refresh their browser

---

### Issue: Streams API not loading

**Symptoms**: Mode detection shows "standalone" when embedded

**Possible Causes**:
1. Streams API script not loaded
2. Amazon Connect CCP not initialized
3. Wrong Connect instance URL

**Solutions**:

1. **Verify Streams API script** in `app/templates/index.html`:
   ```html
   <script src="https://unt-sample-cicd-instance-sab-test.my.connect.aws/connect/static/connect-streams-min.js"></script>
   ```

2. **Check browser console** for Streams API errors:
   - Open DevTools (F12)
   - Go to Console tab
   - Look for errors related to `connect.core.initCCP`

3. **Verify Connect instance URL**:
   ```bash
   eb printenv | grep CONNECT_INSTANCE_URL
   
   # Should return: https://unt-sample-cicd-instance-sab-test.my.connect.aws
   ```

---

## Deployment Issues

### Issue: "502 Bad Gateway" after deployment

**Symptoms**: CloudFront returns 502 error

**Possible Causes**:
1. Elastic Beanstalk environment is starting up
2. Application failed to start
3. Port configuration is incorrect

**Solutions**:

1. **Wait 5 minutes**: Environment takes time to start

2. **Check Elastic Beanstalk health**:
   ```bash
   eb status
   
   # Should show: Health: Green
   ```

3. **Check application logs**:
   ```bash
   eb logs
   
   # Look for startup errors
   ```

4. **Verify port configuration** in `run.py`:
   ```python
   port = int(os.environ.get('PORT', 8000))
   app.run(host='0.0.0.0', port=port)
   ```

---

### Issue: Environment variables not set

**Symptoms**: Application errors related to missing configuration

**Possible Causes**:
1. Environment variables not configured in Elastic Beanstalk
2. Typo in variable names

**Solutions**:

1. **List current environment variables**:
   ```bash
   eb printenv
   ```

2. **Set missing variables**:
   ```bash
   eb setenv AWS_REGION=us-east-1 \
             CONNECT_INSTANCE_ID=6091de37-993e-45c8-9637-e9e3a0af5b23 \
             CONNECT_INSTANCE_URL=https://unt-sample-cicd-instance-sab-test.my.connect.aws \
             FLASK_SECRET_KEY=<your-secret-key>
   ```

3. **Verify in AWS Console**:
   - Go to Elastic Beanstalk console
   - Select environment
   - Configuration → Software → Environment properties

---

### Issue: CloudFront caching old content

**Symptoms**: Changes not visible after deployment

**Possible Causes**:
1. CloudFront cache not invalidated
2. Browser cache

**Solutions**:

1. **Invalidate CloudFront cache**:
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id E2ZQ9PY5KN8UMB \
     --paths "/*"
   ```

2. **Clear browser cache**:
   - Press Ctrl+Shift+R (Windows/Linux)
   - Press Cmd+Shift+R (Mac)

3. **Note**: Only invalidate when frontend files change (HTML, CSS, JS, images). Backend Python changes don't require invalidation.

---

## AWS API Issues

### Issue: "Rate limit exceeded" error

**Symptoms**: API calls fail with rate limit error

**Cause**: Too many API calls in short time period

**Solutions**:

1. **Increase refresh interval**:
   - Current: 15 seconds
   - Recommended: 30 seconds for high-traffic scenarios

2. **Implement exponential backoff** in `app/clients/connect_client.py`:
   ```python
   import time
   from botocore.exceptions import ClientError
   
   def call_with_retry(func, *args, **kwargs):
       max_retries = 3
       for i in range(max_retries):
           try:
               return func(*args, **kwargs)
           except ClientError as e:
               if e.response['Error']['Code'] == 'ThrottlingException':
                   time.sleep(2 ** i)  # Exponential backoff
               else:
                   raise
   ```

3. **Monitor API usage** in CloudWatch:
   - Go to CloudWatch → Metrics
   - Select Connect → API Usage
   - Check request counts

---

### Issue: "Access Denied" error

**Symptoms**: API calls fail with permission error

**Cause**: IAM role doesn't have required permissions

**Solutions**:

1. **Verify IAM role permissions**:
   ```bash
   aws iam get-role-policy \
     --role-name aws-elasticbeanstalk-ec2-role \
     --policy-name ConnectAccess
   ```

2. **Add missing permissions**:
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
           "connect:GetMetricDataV2"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **Attach policy to role**:
   ```bash
   aws iam put-role-policy \
     --role-name aws-elasticbeanstalk-ec2-role \
     --policy-name ConnectAccess \
     --policy-document file://connect-policy.json
   ```

---

### Issue: "OrConditions cannot be empty" error

**Symptoms**: GetMetricDataV2 API call fails

**Cause**: Empty filter conditions in API request

**Solution**: This has been fixed in the code. Ensure you're using the latest version:

```python
# In app/services/queue_service.py
filters = [
    {
        'FilterKey': 'QUEUE',
        'FilterValues': queue_arns
    }
]

# Don't use OrConditions if empty
```

---

## Performance Issues

### Issue: Slow page load times

**Symptoms**: Queue view takes >5 seconds to load

**Possible Causes**:
1. Too many API calls
2. Large number of queues
3. Network latency

**Solutions**:

1. **Optimize API calls**: Batch requests where possible

2. **Implement caching** for routing profile data:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def get_routing_profile(profile_id):
       # Cache routing profile for 5 minutes
       pass
   ```

3. **Use CloudFront edge locations**: Already configured

4. **Monitor performance** in CloudWatch:
   - Go to CloudWatch → Metrics
   - Select Elastic Beanstalk → Environment metrics
   - Check response times

---

### Issue: High AWS costs

**Symptoms**: Unexpected AWS charges

**Possible Causes**:
1. Too many API calls
2. High data transfer
3. Unused resources

**Solutions**:

1. **Review cost breakdown** in `docs/COST_ANALYSIS.md`

2. **Optimize refresh interval**:
   - Current: 15 seconds = $0.38/agent/month
   - Alternative: 30 seconds = $0.19/agent/month

3. **Monitor costs** in AWS Cost Explorer:
   - Go to AWS Cost Management → Cost Explorer
   - Filter by service: Connect, Elastic Beanstalk, CloudFront
   - Check daily costs

4. **Set up billing alerts**:
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name high-connect-costs \
     --alarm-description "Alert when Connect costs exceed $50" \
     --metric-name EstimatedCharges \
     --namespace AWS/Billing \
     --statistic Maximum \
     --period 86400 \
     --evaluation-periods 1 \
     --threshold 50 \
     --comparison-operator GreaterThanThreshold
   ```

---

## Getting Help

If you're still experiencing issues:

1. **Check CloudWatch Logs**:
   ```bash
   eb logs
   ```

2. **Enable debug mode** (local development only):
   ```python
   # In run.py
   app.run(debug=True)
   ```

3. **Test API calls manually**:
   ```bash
   # Test Connect API
   aws connect search-users \
     --instance-id 6091de37-993e-45c8-9637-e9e3a0af5b23 \
     --search-criteria '{"StringCondition":{"FieldName":"Username","Value":"Sabiha","ComparisonType":"EXACT"}}' \
     --region us-east-1
   ```

4. **Review documentation**:
   - `docs/ARCHITECTURE.md` - System architecture
   - `docs/DEPLOYMENT.md` - Deployment guide
   - `docs/API_REFERENCE.md` - API endpoints
   - `docs/COST_ANALYSIS.md` - Cost breakdown

5. **Contact AWS Support**: For AWS-specific issues (API limits, permissions, etc.)

---

## Additional Resources

- [AWS Connect Documentation](https://docs.aws.amazon.com/connect/)
- [Elastic Beanstalk Documentation](https://docs.aws.amazon.com/elasticbeanstalk/)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [AWS Support](https://console.aws.amazon.com/support/)
