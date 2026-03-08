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
    to the agent: the queue name and how many calls are waiting.
    
    Attributes:
        queue_id: Amazon Connect queue ID (UUID)
        queue_name: Human-readable queue name (e.g., "Customer Support")
        contacts_in_queue: Number of calls currently waiting in the queue
        error: Error message if we couldn't get data for this queue (None if successful)
    
    Example:
        queue = QueueMetrics(
            queue_id='queue-123',
            queue_name='Customer Support',
            contacts_in_queue=5,
            error=None
        )
        
        print(f"{queue.queue_name}: {queue.contacts_in_queue} calls waiting")
        # Output: Customer Support: 5 calls waiting
    """
    queue_id: str
    queue_name: str
    contacts_in_queue: int
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
    
    def get_queue_metrics(self, queue_ids: List[str]) -> List[QueueMetrics]:
        """
        Get metrics for multiple queues with names and call counts.
        
        This is the main method you'll use. It:
        1. Fetches queue details (names) in parallel for speed
        2. Gets current metrics (call counts) for all queues
        3. Combines the data into QueueMetrics objects
        4. Sorts by call count (busiest first)
        5. Handles errors gracefully (marks failed queues with error message)
        
        Args:
            queue_ids: List of queue IDs to get metrics for
        
        Returns:
            List of QueueMetrics objects, sorted by contacts_in_queue (descending)
            Queues with errors are included but marked with error message
        
        Example:
            service = QueueService()
            queue_ids = ['queue-1', 'queue-2', 'queue-3']
            
            metrics = service.get_queue_metrics(queue_ids)
            
            for queue in metrics:
                if queue.error:
                    print(f"{queue.queue_id}: Error - {queue.error}")
                else:
                    print(f"{queue.queue_name}: {queue.contacts_in_queue} calls")
            
            # Output (sorted by call count):
            # Customer Support: 10 calls
            # Technical Support: 5 calls
            # Billing: 2 calls
        """
        logger.info(f"Getting metrics for {len(queue_ids)} queue(s)")
        
        if not queue_ids:
            logger.warning("No queue IDs provided")
            return []
        
        # Step 1: Fetch queue details (names) in parallel
        logger.info("Step 1: Fetching queue details in parallel...")
        queue_details = self._fetch_queue_details_parallel(queue_ids)
        
        # Step 2: Get current metrics (call counts) for all queues
        logger.info("Step 2: Fetching current metrics...")
        metrics_data = self._fetch_current_metrics(queue_ids)
        
        # Step 3: Combine queue details with metrics
        logger.info("Step 3: Combining data...")
        queue_metrics_list = self._combine_queue_data(queue_details, metrics_data)
        
        # Step 4: Sort by call count (busiest first)
        logger.info("Step 4: Sorting by call count...")
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
    
    def _fetch_current_metrics(self, queue_ids: List[str]) -> dict:
        """
        Fetch current metrics (call counts) for all queues.
        
        This makes a single API call to get metrics for all queues at once.
        Much more efficient than calling for each queue individually!
        
        Args:
            queue_ids: List of queue IDs
        
        Returns:
            Dictionary mapping queue_id to contacts_in_queue count
            Format: {queue_id: 5, queue_id2: 10, ...}
        
        Private method (internal use only).
        """
        try:
            # Get current metrics for all queues in one API call
            response = self.connect_client.get_current_metric_data(queue_ids)
            
            # DEBUG: Log the raw response to see what we're getting
            logger.info(f"DEBUG: Raw API response: {response}")
            
            # Parse the response to extract call counts
            metrics = {}
            for result in response.get('MetricResults', []):
                # DEBUG: Log each result
                logger.info(f"DEBUG: Processing result: {result}")
                
                # Extract queue ID from dimensions
                queue_id = result.get('Dimensions', {}).get('Queue', {}).get('Id')
                
                logger.info(f"DEBUG: Extracted queue_id: {queue_id}")
                
                if not queue_id:
                    continue
                
                # Extract CONTACTS_IN_QUEUE metric
                contacts_in_queue = 0
                for collection in result.get('Collections', []):
                    logger.info(f"DEBUG: Processing collection: {collection}")
                    metric_name = collection.get('Metric', {}).get('Name')
                    if metric_name == 'CONTACTS_IN_QUEUE':
                        contacts_in_queue = int(collection.get('Value', 0))
                        logger.info(f"DEBUG: Found CONTACTS_IN_QUEUE = {contacts_in_queue} for queue {queue_id}")
                        break
                
                metrics[queue_id] = contacts_in_queue
                logger.info(f"DEBUG: Added to metrics dict: {queue_id} = {contacts_in_queue}")
            
            logger.info(f"DEBUG: Final metrics dict: {metrics}")
            logger.info(f"✓ Retrieved metrics for {len(metrics)} queue(s)")
            return metrics
            
        except ConnectAPIException as e:
            logger.error(f"Error fetching current metrics: {e}")
            # Return empty dict on error - queues will show 0 calls
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching metrics: {e}")
            return {}
    
    def _combine_queue_data(
        self, 
        queue_details: dict, 
        metrics_data: dict
    ) -> List[QueueMetrics]:
        """
        Combine queue details with metrics data.
        
        This merges the queue names (from queue_details) with call counts
        (from metrics_data) into QueueMetrics objects.
        
        Args:
            queue_details: Dictionary of queue details {queue_id: details}
            metrics_data: Dictionary of metrics {queue_id: call_count}
        
        Returns:
            List of QueueMetrics objects
        
        Private method (internal use only).
        """
        queue_metrics_list = []
        
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
                # Create QueueMetrics with data
                queue_name = details.get('Name', f"Queue {queue_id}")
                contacts_in_queue = metrics_data.get(queue_id, 0)
                
                queue_metrics = QueueMetrics(
                    queue_id=queue_id,
                    queue_name=queue_name,
                    contacts_in_queue=contacts_in_queue,
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
