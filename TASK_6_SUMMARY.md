# Task 6 Complete: Amazon Connect API Client Wrapper ✅

## What We Built

We created a comprehensive Python wrapper for the Amazon Connect API using boto3 (AWS SDK for Python). This client simplifies interacting with Amazon Connect and includes robust error handling and logging.

## File Created

**`app/clients/connect_client.py`** - Complete API client with:
- 7 core API methods
- 5 custom exception classes
- Comprehensive error handling
- Detailed logging
- Educational comments explaining each API call

## Core API Methods

### 1. `search_users(username)` - Find Agents

**Purpose**: Search for agents by username

**Amazon Connect API**: `SearchUsers`

**What it does:**
- Searches for users matching the exact username
- Returns list of matching users with their details

**Example:**
```python
client = ConnectClient()
users = client.search_users('john.doe')
# Returns: [{'UserId': 'abc-123', 'Username': 'john.doe', ...}]
```

**Use case**: When you have an agent's username from Streams API and need to find their user ID

---

### 2. `describe_user(user_id)` - Get Agent Details

**Purpose**: Get full details about a specific agent

**Amazon Connect API**: `DescribeUser`

**What it does:**
- Retrieves complete user information
- Includes routing profile ID, security profiles, identity info

**Example:**
```python
user = client.describe_user('abc-123')
routing_profile_id = user['RoutingProfileId']
agent_name = user['IdentityInfo']['FirstName']
```

**Use case**: After finding a user, get their routing profile to see which queues they handle

---

### 3. `describe_routing_profile(routing_profile_id)` - Get Routing Profile

**Purpose**: Get details about a routing profile

**Amazon Connect API**: `DescribeRoutingProfile`

**What it does:**
- Retrieves routing profile information
- Shows profile name, description, media types supported

**Example:**
```python
profile = client.describe_routing_profile('profile-123')
profile_name = profile['Name']  # e.g., "Basic Routing Profile"
```

**Use case**: Understanding which routing profile an agent is assigned to

---

### 4. `list_routing_profile_queues(routing_profile_id)` - Get Assigned Queues

**Purpose**: List all queues in a routing profile

**Amazon Connect API**: `ListRoutingProfileQueues`

**What it does:**
- Returns all queues assigned to the routing profile
- Includes queue IDs, names, priorities, and delays
- Automatically handles pagination

**Example:**
```python
queues = client.list_routing_profile_queues('profile-123')
for queue in queues:
    print(f"Queue: {queue['QueueName']}, Priority: {queue['Priority']}")
```

**Use case**: Finding which queues an agent handles based on their routing profile

---

### 5. `describe_queue(queue_id)` - Get Queue Details

**Purpose**: Get information about a specific queue

**Amazon Connect API**: `DescribeQueue`

**What it does:**
- Retrieves queue details including name, description, status
- Shows queue configuration

**Example:**
```python
queue = client.describe_queue('queue-123')
queue_name = queue['Name']  # e.g., "Customer Support"
status = queue['Status']     # ENABLED or DISABLED
```

**Use case**: Getting the human-readable name for a queue ID

---

### 6. `get_current_metric_data(queue_ids)` - Get Real-Time Metrics

**Purpose**: Get current metrics (call counts) for queues

**Amazon Connect API**: `GetCurrentMetricData`

**What it does:**
- Retrieves real-time metrics for specified queues
- Returns number of contacts waiting in each queue
- Supports multiple queues in one call

**Example:**
```python
metrics = client.get_current_metric_data(['queue-1', 'queue-2'])
for result in metrics['MetricResults']:
    queue_name = result['Dimensions']['Queue']['Name']
    for collection in result['Collections']:
        if collection['Metric']['Name'] == 'CONTACTS_IN_QUEUE':
            count = collection['Value']
            print(f"{queue_name}: {count} calls waiting")
```

**Use case**: Showing agents how many calls are waiting in their queues

---

## Custom Exception Classes

We created specific exceptions for different error scenarios:

### 1. `ConnectAPIException` (Base)
- Base class for all Amazon Connect API errors
- Catch this to handle any Connect-related error

### 2. `AgentNotFoundException`
- Raised when username not found
- Helps distinguish "not found" from other errors

### 3. `InvalidInstanceException`
- Raised when instance ID is invalid
- Catches configuration errors early

### 4. `AuthenticationException`
- Raised when AWS credentials fail
- Indicates IAM permission issues

### 5. `RateLimitException`
- Raised when API rate limits exceeded
- Allows retry logic for throttling

## Error Handling

Every method includes comprehensive error handling:

```python
try:
    users = client.search_users('john.doe')
except AgentNotFoundException:
    print("Agent not found - check username")
except AuthenticationException:
    print("AWS credentials invalid - check IAM permissions")
except RateLimitException:
    print("Too many requests - wait and retry")
except ConnectAPIException as e:
    print(f"API error: {e}")
```

## Logging

All methods include detailed logging:

```python
logger.info("Searching for user: john.doe")
logger.info("✓ Found 1 user(s) matching 'john.doe'")
logger.error("AWS API error: AccessDeniedException")
```

**View logs:**
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## How the APIs Work Together

### Complete Flow: Username → Queue Metrics

```python
# 1. Search for agent by username
users = client.search_users('john.doe')
user_id = users[0]['UserId']

# 2. Get agent details
user = client.describe_user(user_id)
routing_profile_id = user['RoutingProfileId']

# 3. Get routing profile
profile = client.describe_routing_profile(routing_profile_id)

# 4. List queues in routing profile
queues = client.list_routing_profile_queues(routing_profile_id)
queue_ids = [q['QueueId'] for q in queues]

# 5. Get queue details (names)
queue_names = {}
for queue_id in queue_ids:
    queue = client.describe_queue(queue_id)
    queue_names[queue_id] = queue['Name']

# 6. Get current metrics (call counts)
metrics = client.get_current_metric_data(queue_ids)

# 7. Display results
for result in metrics['MetricResults']:
    queue_id = result['Dimensions']['Queue']['Id']
    queue_name = queue_names[queue_id]
    for collection in result['Collections']:
        if collection['Metric']['Name'] == 'CONTACTS_IN_QUEUE':
            count = collection['Value']
            print(f"{queue_name}: {count} calls")
```

## IAM Permissions Required

Your AWS credentials need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:SearchUsers",
        "connect:DescribeUser",
        "connect:DescribeRoutingProfile",
        "connect:ListRoutingProfileQueues",
        "connect:DescribeQueue",
        "connect:GetCurrentMetricData"
      ],
      "Resource": "arn:aws:connect:*:*:instance/*"
    }
  ]
}
```

## Configuration

The client uses settings from `config/settings.py`:

```python
# Automatically uses these from .env:
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
CONNECT_INSTANCE_ID=your-instance-id
```

## Testing the Client

Create a test script:

```python
from app.clients.connect_client import ConnectClient

# Initialize client
client = ConnectClient()

# Test search
try:
    users = client.search_users('test-agent')
    print(f"Found {len(users)} user(s)")
    
    if users:
        user_id = users[0]['UserId']
        user = client.describe_user(user_id)
        print(f"Agent: {user['Username']}")
        print(f"Routing Profile: {user['RoutingProfileId']}")
        
except Exception as e:
    print(f"Error: {e}")
```

## Common API Patterns

### Pagination
Some APIs return paginated results. The client handles this automatically:

```python
# list_routing_profile_queues handles pagination internally
queues = client.list_routing_profile_queues(profile_id)
# Returns ALL queues, not just first page
```

### Batch Operations
Get metrics for multiple queues at once:

```python
# Efficient: One API call for multiple queues
metrics = client.get_current_metric_data(['queue-1', 'queue-2', 'queue-3'])

# Inefficient: Multiple API calls
# Don't do this!
```

### Error Recovery
Handle transient errors:

```python
import time

def search_with_retry(username, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.search_users(username)
        except RateLimitException:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

## What You Learned

1. **AWS SDK (boto3)**: How to use AWS SDK for Python
2. **API Wrappers**: Creating clean interfaces for complex APIs
3. **Error Handling**: Catching and managing different error types
4. **Logging**: Tracking operations for debugging
5. **Pagination**: Handling paginated API responses
6. **Amazon Connect APIs**: Understanding the Connect API structure

## Next Steps

This client will be used by:
- **Task 7**: Agent Service (business logic layer)
- **Task 9**: Queue Service (queue metrics logic)
- **Task 10**: Flask routes (web endpoints)

## Quick Reference

### Initialize Client
```python
from app.clients.connect_client import ConnectClient
client = ConnectClient()
```

### Search Agent
```python
users = client.search_users('username')
```

### Get Agent's Queues
```python
user = client.describe_user(user_id)
queues = client.list_routing_profile_queues(user['RoutingProfileId'])
```

### Get Queue Metrics
```python
metrics = client.get_current_metric_data(queue_ids)
```

### Handle Errors
```python
from app.clients.connect_client import AgentNotFoundException

try:
    users = client.search_users('username')
except AgentNotFoundException:
    print("Agent not found")
```
