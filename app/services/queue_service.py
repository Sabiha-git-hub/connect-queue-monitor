"""
Queue Service - Business Logic for Queue Metrics

This module provides high-level business logic for queue operations.
It retrieves queue details and current metrics (call counts), combining
them into a single, easy-to-use data structure.

Key Concepts for Beginners:
- Queue Metrics: Real-time data about queues (how many calls waiting)
- Parallel Processing: Fetching multiple queue details at the same time (faster!)
- Graceful Degradation: If one queue fails, others still work
- Sorting: Ordering queues by call count (busiest first)

Why This Matters:
Agents need to see which queues are busiest so they can prioritize their work.
This service combines queue names with call counts and sorts them for easy viewing.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.clients.connect_client import ConnectClient, ConnectAPIException

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class QueueMetrics:
    """
    Data class representing queue metrics.
    
    This stores all the information about a queue that we want to display
    to the agent: the queue name, calls waiting, and agent-specific metrics.
    
    Attributes:
        queue_id: Amazon Connect queue ID (UUID)
        queue_name: Human-readable queue name (e.g., "Customer Support")
        contacts_in_queue: Number of calls currently waiting in the queue
        calls_handled: Number of calls handled by this agent in this queue today
        calls_transferred_out: Number of calls transferred out by this agent from this queue today
        available_agents: Number of agents currently available for this queue
        non_productive_agents: Number of agents in ACW or other non-productive states for this queue
        error: Error message if we couldn't get data for this queue (None if successful)
    
    Example:
        queue = QueueMetrics(
            queue_id='queue-123',
            queue_name='Customer Support',
            contacts_in_queue=5,
            calls_handled=15,
            calls_transferred_out=3,
            available_agents=4,
            non_productive_agents=2,
            error=None
        )
        
        print(f"{queue.queue_name}: {queue.contacts_in_queue} calls waiting")
        # Output: Customer Support: 5 calls waiting
    """
    queue_id: str
    queue_name: str
    contacts_in_queue: int
    calls_handled: int = 0
    calls_transferred_out: int = 0
    available_agents: int = 0
    non_productive_agents: int = 0
    error: Optional[str] = None


class QueueService:
    """
    Service class for queue-related business operations.
    
    This class provides high-level methods for working with queues.
    It combines queue details (names) with current metrics (call counts)
    and handles errors gracefully.
    
    Key Features:
    - Parallel queue detail fetching (faster than sequential)
    - Graceful error handling (one queue failure doesn't break everything)
    - Automatic sorting by call count (busiest queues first)
    """
    
    def __init__(self, connect_client: Optional[ConnectClient] = None):
        """
        Initialize the Queue Service.
        
        Args:
            connect_client: Optional ConnectClient instance.
                          If not provided, creates a new one.
        
        Example:
            # Use default client
            service = QueueService()
            
            # Or provide your own client
            client = ConnectClient(region_name='us-west-2')
            service = QueueService(connect_client=client)
        """
        self.connect_client = connect_client or ConnectClient()
        logger.info("QueueService initialized")
    
    def get_queue_metrics(self, queue_ids: List[str], agent_id: Optional[str] = None) -> List[QueueMetrics]:
        """
        Get metrics for multiple queues with names, call counts, and agent-specific metrics.
        
        This is the main method you'll use. It:
        1. Fetches queue details (names) in parallel for speed
        2. Gets current metrics (call counts, agent availability) for all queues
        3. Gets historical agent metrics (calls handled, missed, transferred) if agent_id provided
        4. Combines the data into QueueMetrics objects
        5. Sorts by call count (busiest first)
        6. Handles errors gracefully (marks failed queues with error message)
        
        Args:
            queue_ids: List of queue IDs to get metrics for
            agent_id: Optional agent ID to fetch agent-specific metrics
        
        Returns:
            List of QueueMetrics objects, sorted by contacts_in_queue (descending)
            Queues with errors are included but marked with error message
        
        Example:
            service = QueueService()
            queue_ids = ['queue-1', 'queue-2', 'queue-3']
            
            metrics = service.get_queue_metrics(queue_ids, agent_id='agent-123')
            
            for queue in metrics:
                if queue.error:
                    print(f"{queue.queue_id}: Error - {queue.error}")
                else:
                    print(f"{queue.queue_name}: {queue.contacts_in_queue} calls, "
                          f"{queue.calls_handled} handled today, "
                          f"{queue.available_agents} agents available")
        """
        logger.info(f"Getting metrics for {len(queue_ids)} queue(s)")
        
        if not queue_ids:
            logger.warning("No queue IDs provided")
            return []
        
        # Step 1: Fetch queue details (names) in parallel
        logger.info("Step 1: Fetching queue details in parallel...")
        queue_details = self._fetch_queue_details_parallel(queue_ids)
        
        # Step 2: Get current metrics (call counts, agent availability) for all queues
        logger.info("Step 2: Fetching current metrics...")
        metrics_data = self._fetch_current_metrics(queue_ids)
        
        # Step 3: Get historical agent metrics if agent_id provided
        agent_metrics_data = {}
        if agent_id:
            logger.info("Step 3: Fetching historical agent metrics...")
            agent_metrics_data = self._fetch_agent_metrics(queue_ids, agent_id)
        else:
            logger.info("Step 3: Skipping agent metrics (no agent_id provided)")
        
        # Step 4: Combine queue details with metrics
        logger.info("Step 4: Combining data...")
        queue_metrics_list = self._combine_queue_data(queue_details, metrics_data, agent_metrics_data)
        
        # Step 5: Sort by call count (busiest first)
        logger.info("Step 5: Sorting by call count...")
        sorted_metrics = self._sort_by_call_count(queue_metrics_list)
        
        logger.info(f"✓ Successfully retrieved metrics for {len(sorted_metrics)} queue(s)")
        return sorted_metrics
    
    def _fetch_queue_details_parallel(self, queue_ids: List[str]) -> dict:
        """
        Fetch queue details for multiple queues in parallel.
        
        Why parallel? If you have 10 queues and each API call takes 0.5 seconds:
        - Sequential: 10 × 0.5 = 5 seconds
        - Parallel: ~0.5 seconds (all at once!)
        
        This uses ThreadPoolExecutor to make multiple API calls simultaneously.
        
        Args:
            queue_ids: List of queue IDs
        
        Returns:
            Dictionary mapping queue_id to queue details
            Format: {queue_id: {'Name': 'Queue Name', ...}}
            Failed queues are marked with error
        
        Private method (internal use only).
        """
        queue_details = {}
        
        # Use ThreadPoolExecutor for parallel API calls
        # max_workers=10 means up to 10 concurrent API calls
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all queue detail requests
            future_to_queue_id = {
                executor.submit(self._fetch_single_queue_detail, queue_id): queue_id
                for queue_id in queue_ids
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_queue_id):
                queue_id = future_to_queue_id[future]
                try:
                    queue_detail = future.result()
                    queue_details[queue_id] = queue_detail
                except Exception as e:
                    logger.error(f"Error fetching details for queue {queue_id}: {e}")
                    # Mark this queue with an error
                    queue_details[queue_id] = {
                        'error': f"Failed to fetch queue details: {str(e)}"
                    }
        
        logger.info(f"✓ Fetched details for {len(queue_details)} queue(s)")
        return queue_details
    
    def _fetch_single_queue_detail(self, queue_id: str) -> dict:
        """
        Fetch details for a single queue.
        
        This is called by _fetch_queue_details_parallel for each queue.
        
        Args:
            queue_id: Queue ID to fetch
        
        Returns:
            Queue details dictionary
        
        Raises:
            ConnectAPIException: If API call fails
        
        Private method (internal use only).
        """
        return self.connect_client.describe_queue(queue_id)
    
    def _fetch_agent_metrics(self, queue_ids: List[str], agent_id: str) -> dict:
        """
        Fetch historical agent metrics for queues (calls handled, missed, transferred).
        
        This fetches metrics from midnight (EST) to now for the specified agent and queues.
        
        Args:
            queue_ids: List of queue IDs
            agent_id: Agent ID to fetch metrics for
        
        Returns:
            Dictionary mapping queue_id to agent metrics dict
            Format: {
                queue_id: {
                    'calls_handled': 15,
                    'calls_missed': 2,
                    'calls_transferred_out': 3
                }
            }
        
        Private method (internal use only).
        """
        try:
            from datetime import datetime, timezone
            import pytz
            
            # Get midnight EST today
            est = pytz.timezone('America/New_York')
            now_est = datetime.now(est)
            midnight_est = now_est.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Convert to UTC for API
            start_time = midnight_est.astimezone(timezone.utc).isoformat()
            end_time = now_est.astimezone(timezone.utc).isoformat()
            
            logger.info(f"Fetching agent metrics from {start_time} to {end_time}")
            logger.info(f"DEBUG: Agent ID: {agent_id}")
            logger.info(f"DEBUG: Queue IDs: {queue_ids}")
            
            # Build filters for agent and queues
            filters = [
                {'FilterKey': 'AGENT', 'FilterValues': [agent_id]},
                {'FilterKey': 'QUEUE', 'FilterValues': queue_ids}
            ]
            
            # Define metrics to fetch
            # Note: CONTACTS_MISSED is not available in GetMetricDataV2
            # We can only get CONTACTS_HANDLED and CONTACTS_TRANSFERRED_OUT
            metrics = [
                {'Name': 'CONTACTS_HANDLED'},
                {'Name': 'CONTACTS_TRANSFERRED_OUT'}
            ]
            
            logger.info(f"DEBUG: Filters: {filters}")
            logger.info(f"DEBUG: Metrics: {metrics}")
            
            # Fetch metrics with queue grouping
            response = self.connect_client.get_metric_data_v2(
                start_time=start_time,
                end_time=end_time,
                filters=filters,
                metrics=metrics,
                groupings=['QUEUE']
            )
            
            logger.info(f"DEBUG: Full API response: {response}")
            logger.info(f"DEBUG: Number of results: {len(response.get('MetricResults', []))}")
            
            # Parse response
            agent_metrics = {}
            for result in response.get('MetricResults', []):
                # Extract queue ID from dimensions
                dimensions = result.get('Dimensions', {})
                queue_id = dimensions.get('QUEUE')
                
                if not queue_id:
                    continue
                
                # Initialize metrics for this queue
                # Note: calls_missed is not available from GetMetricDataV2 API
                queue_agent_metrics = {
                    'calls_handled': 0,
                    'calls_transferred_out': 0
                }
                
                # Extract metric values
                for metric_result in result.get('Collections', []):
                    metric_name = metric_result.get('Metric', {}).get('Name')
                    metric_value = int(metric_result.get('Value', 0))
                    
                    if metric_name == 'CONTACTS_HANDLED':
                        queue_agent_metrics['calls_handled'] = metric_value
                    elif metric_name == 'CONTACTS_TRANSFERRED_OUT':
                        queue_agent_metrics['calls_transferred_out'] = metric_value
                
                agent_metrics[queue_id] = queue_agent_metrics
                logger.info(f"DEBUG: Agent metrics for queue {queue_id}: {queue_agent_metrics}")
            
            logger.info(f"✓ Retrieved agent metrics for {len(agent_metrics)} queue(s)")
            return agent_metrics
            
        except Exception as e:
            logger.error(f"Error fetching agent metrics: {e}")
            # Return empty dict on error
            return {}
    
    def _fetch_current_metrics(self, queue_ids: List[str]) -> dict:
        """
        Fetch current metrics (call counts and agent availability) for all queues.
        
        This makes a single API call to get metrics for all queues at once.
        Much more efficient than calling for each queue individually!
        
        Args:
            queue_ids: List of queue IDs
        
        Returns:
            Dictionary mapping queue_id to metrics dict
            Format: {
                queue_id: {
                    'contacts_in_queue': 5,
                    'available_agents': 3,
                    'non_productive_agents': 2
                }
            }
        
        Private method (internal use only).
        """
        try:
            # Define metrics we want to fetch
            current_metrics = [
                {'Name': 'CONTACTS_IN_QUEUE', 'Unit': 'COUNT'},
                {'Name': 'AGENTS_AVAILABLE', 'Unit': 'COUNT'},
                {'Name': 'AGENTS_NON_PRODUCTIVE', 'Unit': 'COUNT'}
            ]
            
            # Get current metrics for all queues in one API call
            response = self.connect_client.get_current_metric_data(
                queue_ids=queue_ids,
                metrics=current_metrics,
                groupings=['QUEUE']
            )
            
            # DEBUG: Log the raw response to see what we're getting
            logger.info(f"DEBUG: Raw API response: {response}")
            
            # Parse the response to extract metrics
            metrics = {}
            for result in response.get('MetricResults', []):
                # DEBUG: Log each result
                logger.info(f"DEBUG: Processing result: {result}")
                
                # Extract queue ID from dimensions
                queue_id = result.get('Dimensions', {}).get('Queue', {}).get('Id')
                
                logger.info(f"DEBUG: Extracted queue_id: {queue_id}")
                
                if not queue_id:
                    continue
                
                # Initialize metrics for this queue
                queue_metrics = {
                    'contacts_in_queue': 0,
                    'available_agents': 0,
                    'non_productive_agents': 0
                }
                
                # Extract metrics from collections
                for collection in result.get('Collections', []):
                    logger.info(f"DEBUG: Processing collection: {collection}")
                    metric_name = collection.get('Metric', {}).get('Name')
                    metric_value = int(collection.get('Value', 0))
                    
                    if metric_name == 'CONTACTS_IN_QUEUE':
                        queue_metrics['contacts_in_queue'] = metric_value
                        logger.info(f"DEBUG: Found CONTACTS_IN_QUEUE = {metric_value} for queue {queue_id}")
                    elif metric_name == 'AGENTS_AVAILABLE':
                        queue_metrics['available_agents'] = metric_value
                        logger.info(f"DEBUG: Found AGENTS_AVAILABLE = {metric_value} for queue {queue_id}")
                    elif metric_name == 'AGENTS_NON_PRODUCTIVE':
                        queue_metrics['non_productive_agents'] = metric_value
                        logger.info(f"DEBUG: Found AGENTS_NON_PRODUCTIVE = {metric_value} for queue {queue_id}")
                
                metrics[queue_id] = queue_metrics
                logger.info(f"DEBUG: Added to metrics dict: {queue_id} = {queue_metrics}")
            
            logger.info(f"DEBUG: Final metrics dict: {metrics}")
            logger.info(f"✓ Retrieved metrics for {len(metrics)} queue(s)")
            return metrics
            
        except ConnectAPIException as e:
            logger.error(f"Error fetching current metrics: {e}")
            # Return empty dict on error - queues will show 0 for all metrics
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching metrics: {e}")
            return {}
    
    def _combine_queue_data(
        self, 
        queue_details: dict, 
        metrics_data: dict,
        agent_metrics_data: dict = None
    ) -> List[QueueMetrics]:
        """
        Combine queue details with metrics data.
        
        This merges the queue names (from queue_details) with call counts and
        agent metrics into QueueMetrics objects.
        
        Args:
            queue_details: Dictionary of queue details {queue_id: details}
            metrics_data: Dictionary of current metrics {queue_id: metrics_dict}
            agent_metrics_data: Optional dictionary of agent metrics {queue_id: agent_metrics_dict}
        
        Returns:
            List of QueueMetrics objects
        
        Private method (internal use only).
        """
        queue_metrics_list = []
        
        if agent_metrics_data is None:
            agent_metrics_data = {}
        
        for queue_id, details in queue_details.items():
            # Check if this queue had an error
            if 'error' in details:
                # Create QueueMetrics with error
                queue_metrics = QueueMetrics(
                    queue_id=queue_id,
                    queue_name=f"Queue {queue_id}",  # Fallback name
                    contacts_in_queue=0,
                    error=details['error']
                )
            else:
                # Get queue name
                queue_name = details.get('Name', f"Queue {queue_id}")
                
                # Get current metrics
                current_metrics = metrics_data.get(queue_id, {})
                contacts_in_queue = current_metrics.get('contacts_in_queue', 0)
                available_agents = current_metrics.get('available_agents', 0)
                non_productive_agents = current_metrics.get('non_productive_agents', 0)
                
                # Get agent metrics
                agent_metrics = agent_metrics_data.get(queue_id, {})
                calls_handled = agent_metrics.get('calls_handled', 0)
                calls_transferred_out = agent_metrics.get('calls_transferred_out', 0)
                
                # Create QueueMetrics with all data
                queue_metrics = QueueMetrics(
                    queue_id=queue_id,
                    queue_name=queue_name,
                    contacts_in_queue=contacts_in_queue,
                    calls_handled=calls_handled,
                    calls_transferred_out=calls_transferred_out,
                    available_agents=available_agents,
                    non_productive_agents=non_productive_agents,
                    error=None
                )
            
            queue_metrics_list.append(queue_metrics)
        
        return queue_metrics_list
    
    def _sort_by_call_count(self, queue_metrics: List[QueueMetrics]) -> List[QueueMetrics]:
        """
        Sort queues by call count in descending order (busiest first).
        
        Queues with errors are placed at the end.
        
        Args:
            queue_metrics: List of QueueMetrics objects
        
        Returns:
            Sorted list of QueueMetrics objects
        
        Private method (internal use only).
        """
        # Separate queues with and without errors
        valid_queues = [q for q in queue_metrics if q.error is None]
        error_queues = [q for q in queue_metrics if q.error is not None]
        
        # Sort valid queues by call count (descending)
        valid_queues.sort(key=lambda q: q.contacts_in_queue, reverse=True)
        
        # Combine: valid queues first, then error queues
        sorted_list = valid_queues + error_queues
        
        logger.info(f"✓ Sorted {len(valid_queues)} valid queue(s), {len(error_queues)} error(s)")
        return sorted_list
    
    def get_agent_performance_summary(self, agent_id: str) -> dict:
        """
        Get agent's personal performance summary for today.
        
        Fetches aggregate metrics for the agent across all queues:
        - Total calls handled today
        - Total calls transferred today
        - Average handle time
        
        Args:
            agent_id: Agent ID to fetch performance for
        
        Returns:
            Dictionary with agent performance metrics:
            {
                'calls_handled': 25,
                'calls_transferred': 5,
                'average_handle_time': 180.5  # in seconds
            }
        """
        try:
            from datetime import datetime, timezone
            import pytz
            
            # Get midnight EST today
            est = pytz.timezone('America/New_York')
            now_est = datetime.now(est)
            midnight_est = now_est.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Convert to UTC for API
            start_time = midnight_est.astimezone(timezone.utc).isoformat()
            end_time = now_est.astimezone(timezone.utc).isoformat()
            
            logger.info(f"Fetching agent performance summary for agent {agent_id}")
            
            # Build filters for agent only (no queue grouping for summary)
            filters = [
                {'FilterKey': 'AGENT', 'FilterValues': [agent_id]}
            ]
            
            # Define metrics to fetch
            metrics = [
                {'Name': 'CONTACTS_HANDLED'},
                {'Name': 'CONTACTS_TRANSFERRED_OUT'},
                {'Name': 'SUM_HANDLE_TIME'}  # Total handle time in seconds
            ]
            
            # Fetch metrics WITHOUT grouping (aggregate across all queues)
            response = self.connect_client.get_metric_data_v2(
                start_time=start_time,
                end_time=end_time,
                filters=filters,
                metrics=metrics,
                groupings=[]  # No grouping = aggregate
            )
            
            logger.info(f"DEBUG: Agent performance API response: {response}")
            
            # Parse response
            performance = {
                'calls_handled': 0,
                'calls_transferred': 0,
                'average_handle_time': 0.0
            }
            
            total_handle_time = 0.0
            
            for result in response.get('MetricResults', []):
                for metric_result in result.get('Collections', []):
                    metric_name = metric_result.get('Metric', {}).get('Name')
                    metric_value = float(metric_result.get('Value', 0))
                    
                    if metric_name == 'CONTACTS_HANDLED':
                        performance['calls_handled'] = int(metric_value)
                    elif metric_name == 'CONTACTS_TRANSFERRED_OUT':
                        performance['calls_transferred'] = int(metric_value)
                    elif metric_name == 'SUM_HANDLE_TIME':
                        total_handle_time = metric_value
            
            # Calculate average handle time
            if performance['calls_handled'] > 0:
                performance['average_handle_time'] = total_handle_time / performance['calls_handled']
            
            logger.info(f"✓ Agent performance: {performance}")
            return performance
            
        except Exception as e:
            logger.error(f"Error fetching agent performance summary: {e}")
            # Return zeros on error
            return {
                'calls_handled': 0,
                'calls_transferred': 0,
                'average_handle_time': 0.0
            }


# ============================================
# Helper Functions
# ============================================

def create_queue_service() -> QueueService:
    """
    Factory function to create a QueueService instance.
    
    This is a convenience function that creates a service with default settings.
    Use this in your Flask routes for consistency.
    
    Returns:
        Configured QueueService instance
    
    Example:
        # In your Flask route
        from app.services.queue_service import create_queue_service
        
        @app.route('/queues')
        def get_queues():
            service = create_queue_service()
            queue_ids = ['queue-1', 'queue-2']
            metrics = service.get_queue_metrics(queue_ids)
            
            return jsonify([{
                'name': q.queue_name,
                'calls': q.contacts_in_queue,
                'error': q.error
            } for q in metrics])
    """
    return QueueService()
