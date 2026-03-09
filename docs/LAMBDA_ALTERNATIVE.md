# Lambda Alternative Architecture

This guide explains how to migrate the Connect Queue Monitor from Elastic Beanstalk to AWS Lambda + API Gateway.

## Table of Contents
- [Why Consider Lambda?](#why-consider-lambda)
- [Architecture Comparison](#architecture-comparison)
- [Migration Steps](#migration-steps)
- [Code Changes Required](#code-changes-required)
- [Cost Comparison](#cost-comparison)
- [When to Migrate](#when-to-migrate)

## Why Consider Lambda?

Lambda + API Gateway offers several advantages for certain use cases:

1. **Automatic Scaling**: Scales from 0 to thousands of concurrent requests automatically
2. **Pay-per-Use**: Only pay for actual execution time (no idle server costs)
3. **No Server Management**: AWS handles all infrastructure maintenance
4. **High Availability**: Built-in redundancy across multiple availability zones
5. **Better for Sporadic Usage**: Ideal when usage is unpredictable or has long idle periods

However, Lambda also has trade-offs:
- **Cold Starts**: First request after idle period takes 1-3 seconds
- **Stateless**: Cannot maintain session state without external storage (DynamoDB)
- **More Complex**: Requires additional services (DynamoDB, API Gateway, CloudFront)
- **Learning Curve**: More AWS services to understand and configure

## Architecture Comparison

### Current Architecture (Elastic Beanstalk)
```
User Browser
    ↓
CloudFront (HTTPS)
    ↓
Elastic Beanstalk (Flask App)
    ├── Session Storage (in-memory)
    └── AWS Connect API
```

### Lambda Architecture
```
User Browser
    ↓
CloudFront (HTTPS)
    ↓
API Gateway (REST API)
    ↓
Lambda Functions (Python)
    ├── DynamoDB (Session Storage)
    └── AWS Connect API
```

## Migration Steps

### Step 1: Set Up DynamoDB for Sessions

Create a DynamoDB table to store user sessions:

```bash
aws dynamodb create-table \
    --table-name connect-queue-monitor-sessions \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

Table structure:
- **Primary Key**: `session_id` (String)
- **Attributes**: `agent_id`, `agent_name`, `expires_at`, `created_at`
- **TTL**: Enable TTL on `expires_at` field for automatic cleanup

### Step 2: Restructure Code for Lambda

Lambda requires a different code structure. Instead of a Flask app, you'll have individual Lambda functions for each endpoint.

Create a new directory structure:
```
lambda/
├── layers/
│   └── python/
│       └── requirements.txt  # Shared dependencies
├── functions/
│   ├── login/
│   │   └── handler.py        # Login endpoint
│   ├── logout/
│   │   └── handler.py        # Logout endpoint
│   ├── queue_view/
│   │   └── handler.py        # Queue view endpoint
│   └── refresh/
│       └── handler.py        # Refresh endpoint
└── shared/
    ├── connect_client.py     # Reuse existing
    ├── agent_service.py      # Reuse existing
    ├── queue_service.py      # Reuse existing
    └── session_manager.py    # NEW: DynamoDB session handling
```

### Step 3: Create Session Manager

Create `lambda/shared/session_manager.py`:

```python
import boto3
import uuid
from datetime import datetime, timedelta

class SessionManager:
    """Manages user sessions in DynamoDB"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('connect-queue-monitor-sessions')
    
    def create_session(self, agent_id, agent_name):
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        expires_at = int((datetime.now() + timedelta(hours=24)).timestamp())
        
        self.table.put_item(Item={
            'session_id': session_id,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'expires_at': expires_at,
            'created_at': int(datetime.now().timestamp())
        })
        
        return session_id
    
    def get_session(self, session_id):
        """Retrieve session data"""
        response = self.table.get_item(Key={'session_id': session_id})
        return response.get('Item')
    
    def delete_session(self, session_id):
        """Delete a session"""
        self.table.delete_item(Key={'session_id': session_id})
```

### Step 4: Convert Flask Routes to Lambda Handlers

Example: Convert login route to Lambda function.

**Current Flask Route** (`app/routes.py`):
```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    # ... authentication logic ...
    session['agent_id'] = agent_id
    return redirect(url_for('queue_view'))
```

**Lambda Handler** (`lambda/functions/login/handler.py`):
```python
import json
from shared.session_manager import SessionManager
from shared.agent_service import AgentService

def lambda_handler(event, context):
    """Handle login requests"""
    
    # Parse request body
    body = json.loads(event['body'])
    username = body.get('username')
    
    # Authenticate user
    agent_service = AgentService()
    agent = agent_service.get_agent_by_username(username)
    
    if not agent:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': 'Invalid username'})
        }
    
    # Create session
    session_manager = SessionManager()
    session_id = session_manager.create_session(
        agent_id=agent['Id'],
        agent_name=agent['Username']
    )
    
    # Return session cookie
    return {
        'statusCode': 302,
        'headers': {
            'Location': '/queue-view',
            'Set-Cookie': f'session_id={session_id}; Secure; HttpOnly; SameSite=None; Path=/'
        }
    }
```

### Step 5: Create API Gateway

Set up API Gateway to route requests to Lambda functions:

```bash
# Create REST API
aws apigateway create-rest-api \
    --name connect-queue-monitor-api \
    --region us-east-1

# Create resources and methods
# /login (POST) → login Lambda
# /logout (POST) → logout Lambda
# /queue-view (GET) → queue_view Lambda
# /refresh (GET) → refresh Lambda
```

API Gateway configuration:
- **Type**: REST API (not HTTP API, for better CloudFront integration)
- **Authorization**: None (handled by session cookies)
- **CORS**: Enable for CloudFront domain
- **Stage**: `prod`

### Step 6: Create Lambda Functions

Deploy each Lambda function:

```bash
# Package login function
cd lambda/functions/login
zip -r login.zip handler.py ../../shared/

# Create Lambda function
aws lambda create-function \
    --function-name connect-queue-monitor-login \
    --runtime python3.11 \
    --role arn:aws:iam::994911658700:role/lambda-execution-role \
    --handler handler.lambda_handler \
    --zip-file fileb://login.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables="{
        AWS_REGION=us-east-1,
        CONNECT_INSTANCE_ID=6091de37-993e-45c8-9637-e9e3a0af5b23,
        CONNECT_INSTANCE_URL=https://unt-sample-cicd-instance-sab-test.my.connect.aws
    }"

# Repeat for other functions (logout, queue_view, refresh)
```

### Step 7: Create Lambda Layer for Dependencies

Create a Lambda layer for shared dependencies (boto3, pytz, etc.):

```bash
# Create layer directory
mkdir -p lambda/layers/python

# Install dependencies
pip install -r requirements.txt -t lambda/layers/python/

# Package layer
cd lambda/layers
zip -r dependencies.zip python/

# Create layer
aws lambda publish-layer-version \
    --layer-name connect-queue-monitor-dependencies \
    --zip-file fileb://dependencies.zip \
    --compatible-runtimes python3.11
```

Attach layer to all Lambda functions:
```bash
aws lambda update-function-configuration \
    --function-name connect-queue-monitor-login \
    --layers arn:aws:lambda:us-east-1:994911658700:layer:connect-queue-monitor-dependencies:1
```

### Step 8: Configure CloudFront

Update CloudFront distribution to point to API Gateway:

1. **Origin**: Change from Elastic Beanstalk to API Gateway
   - Origin Domain: `<api-id>.execute-api.us-east-1.amazonaws.com`
   - Origin Path: `/prod`

2. **Cache Behavior**: Keep existing settings
   - Cache Policy: CachingDisabled
   - Origin Request Policy: AllViewer

3. **Custom Error Responses**: Add 403/404 redirects to `/login`

### Step 9: Update Static Files

Static files (HTML, CSS, JS) need to be served from S3 + CloudFront:

```bash
# Create S3 bucket for static files
aws s3 mb s3://connect-queue-monitor-static

# Upload static files
aws s3 sync app/static/ s3://connect-queue-monitor-static/static/
aws s3 sync app/templates/ s3://connect-queue-monitor-static/templates/

# Configure bucket for CloudFront access
aws s3api put-bucket-policy \
    --bucket connect-queue-monitor-static \
    --policy file://bucket-policy.json
```

Update CloudFront to have two origins:
- **Origin 1**: API Gateway (for API endpoints)
- **Origin 2**: S3 bucket (for static files)

### Step 10: Test and Deploy

1. Test each Lambda function individually
2. Test API Gateway endpoints
3. Test full flow through CloudFront
4. Monitor CloudWatch logs for errors
5. Set up CloudWatch alarms for failures

## Code Changes Required

### Summary of Changes

1. **Session Management**: Replace Flask sessions with DynamoDB
2. **Request Handling**: Convert Flask routes to Lambda handlers
3. **Response Format**: Return API Gateway-compatible responses
4. **Static Files**: Move to S3 instead of serving from Flask
5. **Environment Variables**: Configure in Lambda instead of Elastic Beanstalk
6. **Logging**: Use CloudWatch Logs instead of Flask logging

### Files to Create

- `lambda/shared/session_manager.py` - DynamoDB session handling
- `lambda/functions/login/handler.py` - Login Lambda
- `lambda/functions/logout/handler.py` - Logout Lambda
- `lambda/functions/queue_view/handler.py` - Queue view Lambda
- `lambda/functions/refresh/handler.py` - Refresh Lambda
- `lambda/layers/python/requirements.txt` - Dependencies layer

### Files to Modify

- `app/clients/connect_client.py` - No changes needed (reuse as-is)
- `app/services/agent_service.py` - No changes needed (reuse as-is)
- `app/services/queue_service.py` - No changes needed (reuse as-is)
- `app/templates/*.html` - Update API endpoint URLs
- `app/static/js/app.js` - Update API endpoint URLs

## Cost Comparison

### Elastic Beanstalk (Current)
- **EC2 Instance**: $8.50/month (t3.micro)
- **Load Balancer**: $8.00/month
- **Data Transfer**: $0.50/month
- **Total**: ~$17/month

### Lambda + API Gateway
- **Lambda Execution**: $0.20/month (100 agents × 480 requests/day)
- **API Gateway**: $3.50/month (144,000 requests/month)
- **DynamoDB**: $1.25/month (sessions table)
- **S3 Storage**: $0.50/month (static files)
- **CloudFront**: $1.00/month (data transfer)
- **Total**: ~$6.45/month

**Savings**: $10.55/month (62% reduction)

However, costs increase with scale:
- **At 500 agents**: Lambda = $32/month, Elastic Beanstalk = $17/month
- **At 1000 agents**: Lambda = $64/month, Elastic Beanstalk = $17/month (until you need to scale EC2)

## When to Migrate

### Migrate to Lambda When:

1. **Cost Optimization**: You have <100 agents and want to minimize costs
2. **Sporadic Usage**: Agents only use the app occasionally (not continuously)
3. **Global Scale**: You need to serve agents in multiple regions
4. **Zero Maintenance**: You want AWS to handle all infrastructure
5. **Compliance**: You need built-in redundancy and high availability

### Stay with Elastic Beanstalk When:

1. **Simplicity**: You want a simple, easy-to-understand architecture
2. **Continuous Usage**: Agents use the app continuously during work hours
3. **Session Complexity**: You need complex session management
4. **Development Speed**: You want to iterate quickly without managing multiple services
5. **Cost Predictability**: You prefer fixed monthly costs over variable usage-based costs

## Recommended Approach

For your current use case (workshop demo with <50 agents):

**Recommendation**: Stay with Elastic Beanstalk

**Reasons**:
1. Simpler architecture (easier to understand and maintain)
2. Lower cost at current scale ($17/month vs $6.45/month is negligible)
3. No cold start delays (better user experience)
4. Easier to debug and troubleshoot
5. Faster development iteration

**Consider Lambda migration when**:
- You reach 500+ agents (cost savings become significant)
- Usage becomes sporadic (agents only use app occasionally)
- You need multi-region deployment
- You have DevOps expertise to manage multiple AWS services

## Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Lambda Pricing Calculator](https://aws.amazon.com/lambda/pricing/)
- [Serverless Framework](https://www.serverless.com/) - Tool to simplify Lambda deployment
