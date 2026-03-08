# Task 9 Complete: Queue Service Business Logic ✅

## What We Built

We created the **Queue Service** - a business logic layer that retrieves queue metrics (call counts) and combines them with queue details. It features parallel processing for speed and graceful error handling.

## File Created

**`app/services/queue_service.py`** - Complete queue service with:
- `QueueMetrics` dataclass for structured queue data
- `QueueService` class with intelligent operations
- **Parallel processing** for faster queue detail fetching
- **Graceful error handling** (partial failures don't break everything)
- **Automatic sorting** by call count (busiest queues first)

## The Problem We're Solving

Agents need to see:
1. **Which queues** they handle (queue names)
2. **How many calls** are waiting in each queue
3. **Which queues are busiest** (sorted by call count)

This requires combining data from multiple API calls and presenting it in a useful way.

## QueueMetrics Dataclass

Structured data container for queue information:

```python
@dataclass
class QueueMetrics:
    queue_id: str              # Amazon Connect queue ID
    queue_name: str            # Human-readable name
    contacts_in_queue: int     # Number of calls waiting
    error: Optional[str]       # Error message if fetch failed
```

**Example:**
```python
queue = QueueMetrics(
    queue_id='queue-123',
    queue_name='Customer Support',
    contacts_in_queue=5,
    error=None
)

print(f"{queue.queue_name}: {queue.contacts_in_queue} calls waiting")
# Output: Customer Support: 5 calls waiting
```

## QueueService Main Method

### `get_queue_metrics(queue_ids)`

**Purpose**: Get complete queue information with call counts

**What it does:**
1. Fetches queue details (names) **in parallel** for speed
2. Gets current metrics (call counts) for all queues
3. Combines the data into QueueMetrics objects
4. Sorts by call count (busiest first)
5. Handles errors gracefully

**Example:**
```python
service = QueueService()
queue_ids = ['queue-1', 'queue-2', 'queue-3']

metrics = service.get_queue_metrics(queue_ids)

for queue in metrics:
    if queue.error:
        print(f"❌ {queue.queue_id}: {queue.error}")
    else:
        print(f"✅ {queue.queue_name}: {queue.contacts_in_queue} calls")

# Output (sorted by call count):
# ✅ Customer Support: 10 calls
# ✅ Technical Support: 5 calls
# ✅ Billing: 2 calls
```

## Key Feature: Parallel Processing

### The Speed Problem

If you have 10 queues and each API call takes 0.5 seconds:

**Sequential (one at a time):**
```
Queue 1: 0.5s
Queue 2: 0.5s
Queue 3: 0.5s
...
Queue 10: 0.5s
Total: 5 seconds ⏱️
```

**Parallel (all at once):**
```
Queue 1, 2, 3, 4, 5, 6, 7, 8, 9, 10: ~0.5s
Total: ~0.5 seconds ⚡
```

### How We Do It

Using Python's `ThreadPoolExecutor`:

```python
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit all requests at once
    futures = {
        executor.submit(fetch_queue, queue_id): queue_id
        for queue_id in queue_ids
    }
    
    # Collect results as they complete
    for future in as_completed(futures):
        result = future.result()
```

**Result**: 10x faster! 🚀

## Key Feature: Graceful Error Handling

### The Problem

What if one queue fails to load? Should the whole page break?

**Bad approach:**
```python
# If queue-2 fails, everything fails
queue1 = get_queue('queue-1')  # ✅ Success
queue2 = get_queue('queue-2')  # ❌ Error - CRASH!
queue3 = get_queue('queue-3')  # Never reached
```

**Our approach:**
```python
# If queue-2 fails, mark it with error and continue
queue1 = get_queue('queue-1')  # ✅ Success
queue2 = get_queue('queue-2')  # ❌ Error - Mark with error message
queue3 = get_queue('queue-3')  # ✅ Success - Still works!
```

### How It Works

```python
try:
    queue_detail = fetch_queue_detail(queue_id)
except Exception as e:
    # Don't crash - mark with error instead
    queue_detail = {'error': f"Failed: {str(e)}"}
```

**Result**: Partial failures don't break the whole page!

## Key Feature: Automatic Sorting

Queues are automatically sorted by call count (busiest first):

```python
# Before sorting
[
    QueueMetrics('Billing', 2 calls),
    QueueMetrics('Customer Support', 10 calls),
    QueueMetrics('Technical Support', 5 calls)
]

# After sorting
[
    QueueMetrics('Customer Support', 10 calls),    # Busiest first
    QueueMetrics('Technical Support', 5 calls),
    QueueMetrics('Billing', 2 calls)
]
```

Queues with errors are placed at the end.

## The Complete Flow

```
Queue IDs
    ↓
Step 1: Fetch Queue Details (Parallel)
    ├─ Queue 1 → describe_queue() → Name: "Customer Support"
    ├─ Queue 2 → describe_queue() → Name: "Technical Support"
    └─ Queue 3 → describe_queue() → Name: "Billing"
    ↓
Step 2: Fetch Current Metrics (Single API Call)
    └─ get_current_metric_data([queue-1, queue-2, queue-3])
       → Queue 1: 10 calls
       → Queue 2: 5 calls
       → Queue 3: 2 calls
    ↓
Step 3: Combine Data
    ├─ QueueMetrics("Customer Support", 10 calls)
    ├─ QueueMetrics("Technical Support", 5 calls)
    └─ QueueMetrics("Billing", 2 calls)
    ↓
Step 4: Sort by Call Count
    ├─ Customer Support: 10 calls (busiest)
    ├─ Technical Support: 5 calls
    └─ Billing: 2 calls
    ↓
Return Sorted List
```

## Internal Methods (Private)

The service uses several private methods (prefixed with `_`):

### `_fetch_queue_details_parallel(queue_ids)`
- Fetches queue details for multiple queues simultaneously
- Uses ThreadPoolExecutor for parallel processing
- Returns dictionary mapping queue_id to details

### `_fetch_single_queue_detail(queue_id)`
- Fetches details for one queue
- Called by parallel fetcher for each queue
- Returns queue details dictionary

### `_fetch_current_metrics(queue_ids)`
- Gets current metrics for all queues in one API call
- Parses response to extract call counts
- Returns dictionary mapping queue_id to call count

### `_combine_queue_data(queue_details, metrics_data)`
- Merges queue names with call counts
- Creates QueueMetrics objects
- Handles queues with errors

### `_sort_by_call_count(queue_metrics)`
- Sorts queues by call count (descending)
- Places error queues at the end
- Returns sorted list

## Usage Example

### Basic Usage
```python
from app.services.queue_service import QueueService

# Create service
service = QueueService()

# Get metrics for queues
queue_ids = ['queue-1', 'queue-2', 'queue-3']
metrics = service.get_queue_metrics(queue_ids)

# Display results
for queue in metrics:
    if queue.error:
        print(f"❌ Error: {queue.error}")
    else:
        print(f"📞 {queue.queue_name}: {queue.contacts_in_queue} calls")
```

### In Flask Route (Task 10)
```python
from flask import jsonify
from app.services.queue_service import create_queue_service

@app.route('/queues')
def get_queues():
    # Get queue IDs from session (agent's assigned queues)
    queue_ids = session.get('queue_ids', [])
    
    # Create service
    service = create_queue_service()
    
    # Get metrics
    metrics = service.get_queue_metrics(queue_ids)
    
    # Return JSON
    return jsonify([{
        'id': q.queue_id,
        'name': q.queue_name,
        'calls': q.contacts_in_queue,
        'error': q.error
    } for q in metrics])
```

## Factory Function

Convenience function for creating service instances:

```python
from app.services.queue_service import create_queue_service

# Easy service creation
service = create_queue_service()
metrics = service.get_queue_metrics(queue_ids)
```

## Error Scenarios Handled

| Scenario | Behavior |
|----------|----------|
| One queue fails to load | Mark with error, continue with others |
| Metrics API fails | All queues show 0 calls |
| Queue name unavailable | Use fallback name "Queue {id}" |
| Empty queue list | Return empty list |
| All queues fail | Return list with all errors marked |

## Performance Comparison

### Sequential vs Parallel

**10 Queues, 0.5s per API call:**

| Approach | Time | Speed |
|----------|------|-------|
| Sequential | 5.0s | 1x |
| Parallel (10 workers) | 0.5s | 10x faster ⚡ |

**Real-world impact:**
- Better user experience (faster page loads)
- Lower perceived latency
- More responsive application

## Architecture Layers

```
Flask Routes (Web Layer)
    ↓
QueueService (Business Logic Layer) ← You are here
    ↓
ConnectClient (API Client Layer)
    ↓
Amazon Connect APIs
```

## What You Learned

1. **Parallel Processing**: Using ThreadPoolExecutor for concurrent operations
2. **Graceful Degradation**: Handling partial failures
3. **Data Combination**: Merging data from multiple sources
4. **Sorting Algorithms**: Organizing data for display
5. **Service Layer Pattern**: High-level business operations

## Testing the Service

Create a test script:

```python
from app.services.queue_service import QueueService

# Initialize service
service = QueueService()

# Test with queue IDs (replace with your actual queue IDs)
queue_ids = ['your-queue-id-1', 'your-queue-id-2']

try:
    metrics = service.get_queue_metrics(queue_ids)
    
    print(f"✅ Retrieved metrics for {len(metrics)} queue(s)")
    print()
    
    for queue in metrics:
        if queue.error:
            print(f"❌ {queue.queue_id}")
            print(f"   Error: {queue.error}")
        else:
            print(f"✅ {queue.queue_name}")
            print(f"   Calls waiting: {queue.contacts_in_queue}")
        print()
        
except Exception as e:
    print(f"❌ Error: {e}")
```

## Next Steps

This service will be used by:
- **Task 10**: Flask routes (queue view endpoint)
- **Task 12**: HTML templates (displaying queue list)
- **Task 13**: JavaScript (AJAX refresh)

## Quick Reference

### Create Service
```python
from app.services.queue_service import QueueService
service = QueueService()
```

### Get Queue Metrics
```python
metrics = service.get_queue_metrics(['queue-1', 'queue-2'])
```

### Access Queue Data
```python
for queue in metrics:
    print(queue.queue_name)
    print(queue.contacts_in_queue)
    print(queue.error)
```

### Check for Errors
```python
if queue.error:
    print(f"Error: {queue.error}")
else:
    print(f"Calls: {queue.contacts_in_queue}")
```
