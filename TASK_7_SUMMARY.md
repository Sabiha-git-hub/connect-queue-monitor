# Task 7 Complete: Agent Service Business Logic ✅

## What We Built

We created the **Agent Service** - a business logic layer that simplifies agent operations by orchestrating multiple API calls into single, easy-to-use methods.

## File Created

**`app/services/agent_service.py`** - Complete service layer with:
- `Agent` dataclass for structured agent data
- `AgentService` class with high-level operations
- Dual-mode support (automatic/manual detection)
- Helper methods for common operations
- Comprehensive error handling and logging

## The Service Layer Concept

### Problem: Too Many API Calls

Without a service layer, getting agent info requires multiple steps:

```python
# In your Flask route - messy!
users = connect_client.search_users('john.doe')
user_id = users[0]['UserId']
user = connect_client.describe_user(user_id)
routing_profile_id = user['RoutingProfileId']
profile = connect_client.describe_routing_profile(routing_profile_id)
queues = connect_client.list_routing_profile_queues(routing_profile_id)
# ... now combine all this data
```

### Solution: Service Layer Orchestration

With the service layer, one method does everything:

```python
# In your Flask route - clean!
service = AgentService()
agent = service.get_agent_by_username('john.doe')
# Done! Agent object has everything you need
```

## Agent Dataclass

Structured data container for agent information:

```python
@dataclass
class Agent:
    user_id: str                    # Amazon Connect user ID
    username: str                   # Agent's username
    routing_profile_id: str         # Routing profile ID
    routing_profile_name: str       # Human-readable profile name
    assigned_queue_ids: List[str]   # List of queue IDs
    detection_mode: str             # 'automatic' or 'manual'
```

**Example:**
```python
agent = Agent(
    user_id='abc-123',
    username='john.doe',
    routing_profile_id='profile-456',
    routing_profile_name='Basic Routing Profile',
    assigned_queue_ids=['queue-1', 'queue-2', 'queue-3'],
    detection_mode='automatic'
)

print(f"Agent: {agent.username}")
print(f"Profile: {agent.routing_profile_name}")
print(f"Handles {len(agent.assigned_queue_ids)} queues")
```

## AgentService Methods

### 1. `get_agent_by_username(username, detection_mode)`

**Purpose**: Get complete agent information in one call

**What it does:**
1. Searches for user by username
2. Gets user details (including routing profile ID)
3. Gets routing profile details (name)
4. Lists queues in routing profile
5. Returns Agent object with all data

**Example:**
```python
service = AgentService()

# Automatic detection (from Streams API)
agent = service.get_agent_by_username('john.doe', 'automatic')

# Manual entry (from login form)
agent = service.get_agent_by_username('jane.smith', 'manual')

# Use the data
print(f"Agent: {agent.username}")
print(f"Profile: {agent.routing_profile_name}")
print(f"Queues: {agent.assigned_queue_ids}")
```

### 2. `validate_agent_exists(username)`

**Purpose**: Quick check if agent exists

**What it does:**
- Searches for username
- Returns True/False
- Doesn't fetch full details (faster)

**Example:**
```python
service = AgentService()

if service.validate_agent_exists('john.doe'):
    print("Agent exists!")
else:
    print("Agent not found")
```

### 3. `get_agent_routing_profile_name(username)`

**Purpose**: Get just the routing profile name

**What it does:**
- Searches for user
- Gets routing profile
- Returns profile name only

**Example:**
```python
service = AgentService()
profile_name = service.get_agent_routing_profile_name('john.doe')
print(f"Routing Profile: {profile_name}")
```

### 4. `get_agent_queue_count(username)`

**Purpose**: Get number of queues assigned to agent

**What it does:**
- Gets full agent info
- Returns count of assigned queues

**Example:**
```python
service = AgentService()
count = service.get_agent_queue_count('john.doe')
print(f"Agent handles {count} queues")
```

## Dual-Mode Support

The service supports two detection modes:

### Automatic Mode (Embedded in Amazon Connect)
```python
# Agent detected via Streams API
agent = service.get_agent_by_username('john.doe', 'automatic')
print(agent.detection_mode)  # 'automatic'
```

### Manual Mode (Standalone)
```python
# Agent entered username in login form
agent = service.get_agent_by_username('john.doe', 'manual')
print(agent.detection_mode)  # 'manual'
```

## The Orchestration Flow

When you call `get_agent_by_username()`, here's what happens:

```
1. Search Users API
   ↓
2. Describe User API
   ↓
3. Describe Routing Profile API
   ↓
4. List Routing Profile Queues API
   ↓
5. Create Agent Object
   ↓
6. Return to caller
```

All of this happens automatically in one method call!

## Error Handling

The service handles errors gracefully:

```python
from app.services.agent_service import AgentService
from app.clients.connect_client import AgentNotFoundException

service = AgentService()

try:
    agent = service.get_agent_by_username('invalid-user')
except AgentNotFoundException:
    print("Agent not found - check username")
except ConnectAPIException as e:
    print(f"API error: {e}")
```

## Factory Function

Convenience function for creating service instances:

```python
from app.services.agent_service import create_agent_service

# In your Flask route
@app.route('/agent/<username>')
def get_agent(username):
    service = create_agent_service()  # Easy!
    agent = service.get_agent_by_username(username)
    
    return jsonify({
        'username': agent.username,
        'profile': agent.routing_profile_name,
        'queues': agent.assigned_queue_ids
    })
```

## Benefits of Service Layer

1. **Simplification**: One method call instead of 4+ API calls
2. **Reusability**: Use same logic in multiple places
3. **Maintainability**: Change logic in one place
4. **Testability**: Easy to mock and test
5. **Readability**: Clean, understandable code

## Real-World Analogy

Think of the service layer like ordering at a restaurant:

**Without Service Layer** (ordering ingredients):
- "I need flour"
- "I need eggs"
- "I need milk"
- "I need sugar"
- "Now I'll make a cake myself"

**With Service Layer** (ordering from menu):
- "I want a cake"
- Restaurant handles all the steps!

## Architecture Layers

```
Flask Routes (Web Layer)
    ↓
AgentService (Business Logic Layer) ← You are here
    ↓
ConnectClient (API Client Layer)
    ↓
Amazon Connect APIs
```

## Usage in Flask Routes

This is how you'll use the service in Task 10:

```python
from flask import jsonify
from app.services.agent_service import create_agent_service

@app.route('/agent/login', methods=['POST'])
def agent_login():
    username = request.json.get('username')
    
    # Create service
    service = create_agent_service()
    
    # Get agent info (one call!)
    agent = service.get_agent_by_username(username, 'manual')
    
    # Store in session
    session['agent_username'] = agent.username
    session['detection_mode'] = agent.detection_mode
    
    # Return response
    return jsonify({
        'success': True,
        'agent': {
            'username': agent.username,
            'routing_profile': agent.routing_profile_name,
            'queue_count': len(agent.assigned_queue_ids)
        }
    })
```

## Testing the Service

Create a test script:

```python
from app.services.agent_service import AgentService

# Initialize service
service = AgentService()

# Test with your agent username
try:
    agent = service.get_agent_by_username('your-username')
    
    print(f"✅ Agent found: {agent.username}")
    print(f"   Routing Profile: {agent.routing_profile_name}")
    print(f"   Assigned Queues: {len(agent.assigned_queue_ids)}")
    
    for queue_id in agent.assigned_queue_ids:
        print(f"   - {queue_id}")
        
except Exception as e:
    print(f"❌ Error: {e}")
```

## What You Learned

1. **Service Layer Pattern**: Separating business logic from API calls
2. **Orchestration**: Coordinating multiple operations
3. **Dataclasses**: Structured data containers
4. **Error Handling**: Graceful failure management
5. **Code Organization**: Layered architecture

## Next Steps

This service will be used by:
- **Task 10**: Flask routes (web endpoints)
- **Task 12**: HTML templates (displaying agent info)
- **Task 13**: JavaScript (AJAX requests)

## Quick Reference

### Create Service
```python
from app.services.agent_service import AgentService
service = AgentService()
```

### Get Agent Info
```python
agent = service.get_agent_by_username('username', 'automatic')
```

### Check Agent Exists
```python
exists = service.validate_agent_exists('username')
```

### Get Profile Name
```python
profile = service.get_agent_routing_profile_name('username')
```

### Get Queue Count
```python
count = service.get_agent_queue_count('username')
```
