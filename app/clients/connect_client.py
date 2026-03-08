"""
Amazon Connect API Client Wrapper

This module provides a Python wrapper around the Amazon Connect API using boto3.
It simplifies common operations like finding agents, getting routing profiles,
and retrieving queue metrics.

Key Concepts for Beginners:
- boto3: AWS SDK for Python - lets you interact with AWS services from Python code
- API Client: A class that wraps API calls to make them easier to use
- Error Handling: Catching and managing errors that can occur during API calls
- Logging: Recording what happens for debugging and monitoring

Why This Matters:
The Amazon Connect API has many methods with complex parameters. This wrapper:
1. Simplifies the API calls with easy-to-use methods
2. Handles errors gracefully with custom exceptions
3. Adds logging for troubleshooting
4. Validates inputs before making API calls
"""

import boto3
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError
from config.settings import Config

# Set up logging
# This creates a logger that will help us track what's happening
logger = logging.getLogger(__name__)


class ConnectClient:
    """
    Wrapper class for Amazon Connect API operations.
    
    This class provides simplified methods for common Amazon Connect operations:
    - Searching for agents by username
    - Getting agent details
    - Retrieving routing profiles
    - Listing queues in a routing profile
    - Getting queue metrics (call counts)
    
    All methods include error handling and logging.
    """
    
    def __init__(self, region_name: Optional[str] = None, instance_id: Optional[str] = None):
        """
        Initialize the Amazon Connect client.
        
        Args:
            region_name: AWS region (e.g., 'us-east-1'). Uses Config if not provided.
            instance_id: Amazon Connect instance ID (UUID). Uses Config if not provided.
        
        Raises:
            ValueError: If instance_id is not in valid UUID format
        """
        # Use configuration values if not provided
        self.region_name = region_name or Config.AWS_REGION
        self.instance_id = instance_id or Config.get_instance_id()
        
        logger.info(f"Initializing ConnectClient for region: {self.region_name}")
        logger.info(f"Instance ID: {self.instance_id}")
        
        # Create boto3 client for Amazon Connect
        # This is the low-level client that makes actual API calls
        try:
            client_kwargs = {
                'service_name': 'connect',
                'region_name': self.region_name
            }
            
            # Add credentials if provided in config
            if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
                client_kwargs['aws_access_key_id'] = Config.AWS_ACCESS_KEY_ID
                client_kwargs['aws_secret_access_key'] = Config.AWS_SECRET_ACCESS_KEY
                
                # Add session token if present (for temporary credentials)
                if Config.AWS_SESSION_TOKEN:
                    client_kwargs['aws_session_token'] = Config.AWS_SESSION_TOKEN
            
            self.client = boto3.client(**client_kwargs)
            logger.info("✓ Amazon Connect client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Amazon Connect client: {e}")
            raise AuthenticationException(f"Failed to initialize AWS client: {e}")
    
    def search_users(self, username: str) -> List[Dict]:
        """
        Search for users (agents) by username.
        
        This method uses the SearchUsers API to find agents matching the username.
        Amazon Connect stores agents as "users" in the system.
        
        API Call: connect.search_users()
        Documentation: https://docs.aws.amazon.com/connect/latest/APIReference/API_SearchUsers.html
        
        Args:
            username: The agent's username to search for
        
        Returns:
            List of user dictionaries matching the search
            Each dict contains: UserId, Username, IdentityInfo, RoutingProfileId, etc.
        
        Raises:
            AgentNotFoundException: If no users found matching username
            ConnectAPIException: If API call fails
        
        Example:
            users = client.search_users('john.doe')
            # Returns: [{'UserId': 'abc-123', 'Username': 'john.doe', ...}]
        """
        logger.info(f"Searching for user: {username}")
        
        try:
            # Call the SearchUsers API
            # StringCondition with ComparisonType='EXACT' means exact username match
            response = self.client.search_users(
                InstanceId=self.instance_id,
                SearchCriteria={
                    'StringCondition': {
                        'FieldName': 'Username',
                        'Value': username,
                        'ComparisonType': 'EXACT'  # Must match exactly
                    }
                }
            )
            
            # Extract users from response
            users = response.get('Users', [])
            
            logger.info(f"Found {len(users)} user(s) matching '{username}'")
            
            if not users:
                raise AgentNotFoundException(f"No agent found with username: {username}")
            
            return users
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"AWS API error searching users: {error_code} - {error_message}")
            
            # Handle specific error codes
            if error_code == 'ResourceNotFoundException':
                raise InvalidInstanceException(f"Invalid instance ID: {self.instance_id}")
            elif error_code == 'AccessDeniedException':
                raise AuthenticationException("Access denied. Check IAM permissions.")
            elif error_code == 'ThrottlingException':
                raise RateLimitException("API rate limit exceeded. Please retry later.")
            else:
                raise ConnectAPIException(f"Error searching users: {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            raise ConnectAPIException(f"AWS SDK error: {e}")
    
    def describe_user(self, user_id: str) -> Dict:
        """
        Get detailed information about a specific user (agent).
        
        This method retrieves full details about an agent including their
        routing profile, security profiles, and identity information.
        
        API Call: connect.describe_user()
        Documentation: https://docs.aws.amazon.com/connect/latest/APIReference/API_DescribeUser.html
        
        Args:
            user_id: The unique ID of the user (from search_users)
        
        Returns:
            Dictionary with user details including:
            - Id: User ID
            - Username: Username
            - IdentityInfo: Name, email, etc.
            - RoutingProfileId: ID of assigned routing profile
            - SecurityProfileIds: List of security profile IDs
        
        Raises:
            AgentNotFoundException: If user ID not found
            ConnectAPIException: If API call fails
        
        Example:
            user = client.describe_user('abc-123')
            routing_profile_id = user['RoutingProfileId']
        """
        logger.info(f"Describing user: {user_id}")
        
        try:
            response = self.client.describe_user(
                UserId=user_id,
                InstanceId=self.instance_id
            )
            
            user = response.get('User', {})
            logger.info(f"✓ Retrieved user details for: {user.get('Username')}")
            
            return user
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"AWS API error describing user: {error_code} - {error_message}")
            
            if error_code == 'ResourceNotFoundException':
                raise AgentNotFoundException(f"User not found: {user_id}")
            elif error_code == 'AccessDeniedException':
                raise AuthenticationException("Access denied. Check IAM permissions.")
            else:
                raise ConnectAPIException(f"Error describing user: {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            raise ConnectAPIException(f"AWS SDK error: {e}")
    
    def describe_routing_profile(self, routing_profile_id: str) -> Dict:
        """
        Get details about a routing profile.
        
        A routing profile determines which queues an agent handles and
        the priority/delay for each queue.
        
        API Call: connect.describe_routing_profile()
        Documentation: https://docs.aws.amazon.com/connect/latest/APIReference/API_DescribeRoutingProfile.html
        
        Args:
            routing_profile_id: The ID of the routing profile
        
        Returns:
            Dictionary with routing profile details including:
            - RoutingProfileId: Profile ID
            - Name: Profile name
            - Description: Profile description
            - MediaConcurrencies: Supported media types (voice, chat, task)
            - DefaultOutboundQueueId: Default queue for outbound
        
        Raises:
            ConnectAPIException: If API call fails
        
        Example:
            profile = client.describe_routing_profile('profile-123')
            profile_name = profile['Name']
        """
        logger.info(f"Describing routing profile: {routing_profile_id}")
        
        try:
            response = self.client.describe_routing_profile(
                InstanceId=self.instance_id,
                RoutingProfileId=routing_profile_id
            )
            
            profile = response.get('RoutingProfile', {})
            logger.info(f"✓ Retrieved routing profile: {profile.get('Name')}")
            
            return profile
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"AWS API error describing routing profile: {error_code} - {error_message}")
            
            if error_code == 'ResourceNotFoundException':
                raise ConnectAPIException(f"Routing profile not found: {routing_profile_id}")
            elif error_code == 'AccessDeniedException':
                raise AuthenticationException("Access denied. Check IAM permissions.")
            else:
                raise ConnectAPIException(f"Error describing routing profile: {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            raise ConnectAPIException(f"AWS SDK error: {e}")
    
    def list_routing_profile_queues(self, routing_profile_id: str) -> List[Dict]:
        """
        List all queues associated with a routing profile.
        
        This returns the queue IDs that are assigned to the routing profile.
        Each queue has a priority and delay setting.
        
        API Call: connect.list_routing_profile_queues()
        Documentation: https://docs.aws.amazon.com/connect/latest/APIReference/API_ListRoutingProfileQueues.html
        
        Args:
            routing_profile_id: The ID of the routing profile
        
        Returns:
            List of queue summary dictionaries, each containing:
            - QueueId: Queue ID
            - QueueArn: Queue ARN
            - QueueName: Queue name
            - Priority: Queue priority (1 = highest)
            - Delay: Delay in seconds before routing to this queue
            - Channel: Media channel (VOICE, CHAT, TASK)
        
        Raises:
            ConnectAPIException: If API call fails
        
        Example:
            queues = client.list_routing_profile_queues('profile-123')
            queue_ids = [q['QueueId'] for q in queues]
        """
        logger.info(f"Listing queues for routing profile: {routing_profile_id}")
        
        try:
            # This API supports pagination, but we'll get all results
            all_queues = []
            next_token = None
            
            while True:
                # Build request parameters
                params = {
                    'InstanceId': self.instance_id,
                    'RoutingProfileId': routing_profile_id,
                    'MaxResults': 100  # Maximum allowed per page
                }
                
                if next_token:
                    params['NextToken'] = next_token
                
                # Make API call
                response = self.client.list_routing_profile_queues(**params)
                
                # Add queues from this page
                queues = response.get('RoutingProfileQueueConfigSummaryList', [])
                all_queues.extend(queues)
                
                # Check if there are more pages
                next_token = response.get('NextToken')
                if not next_token:
                    break  # No more pages
            
            logger.info(f"✓ Found {len(all_queues)} queue(s) in routing profile")
            
            return all_queues
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"AWS API error listing routing profile queues: {error_code} - {error_message}")
            
            if error_code == 'ResourceNotFoundException':
                raise ConnectAPIException(f"Routing profile not found: {routing_profile_id}")
            elif error_code == 'AccessDeniedException':
                raise AuthenticationException("Access denied. Check IAM permissions.")
            else:
                raise ConnectAPIException(f"Error listing routing profile queues: {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            raise ConnectAPIException(f"AWS SDK error: {e}")
    
    def describe_queue(self, queue_id: str) -> Dict:
        """
        Get details about a specific queue.
        
        This retrieves queue information including name, description, and status.
        
        API Call: connect.describe_queue()
        Documentation: https://docs.aws.amazon.com/connect/latest/APIReference/API_DescribeQueue.html
        
        Args:
            queue_id: The ID of the queue
        
        Returns:
            Dictionary with queue details including:
            - QueueId: Queue ID
            - QueueArn: Queue ARN
            - Name: Queue name
            - Description: Queue description
            - Status: ENABLED or DISABLED
            - MaxContacts: Maximum contacts in queue
            - OutboundCallerConfig: Outbound caller ID settings
        
        Raises:
            ConnectAPIException: If API call fails
        
        Example:
            queue = client.describe_queue('queue-123')
            queue_name = queue['Name']
        """
        logger.info(f"Describing queue: {queue_id}")
        
        try:
            response = self.client.describe_queue(
                InstanceId=self.instance_id,
                QueueId=queue_id
            )
            
            queue = response.get('Queue', {})
            logger.info(f"✓ Retrieved queue: {queue.get('Name')}")
            
            return queue
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"AWS API error describing queue: {error_code} - {error_message}")
            
            if error_code == 'ResourceNotFoundException':
                raise ConnectAPIException(f"Queue not found: {queue_id}")
            elif error_code == 'AccessDeniedException':
                raise AuthenticationException("Access denied. Check IAM permissions.")
            else:
                raise ConnectAPIException(f"Error describing queue: {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            raise ConnectAPIException(f"AWS SDK error: {e}")
    
    def get_current_metric_data(self, queue_ids: List[str]) -> Dict:
        """
        Get current metrics (real-time data) for queues.
        
        This retrieves real-time metrics like number of contacts in queue,
        available agents, agents on call, etc.
        
        API Call: connect.get_current_metric_data()
        Documentation: https://docs.aws.amazon.com/connect/latest/APIReference/API_GetCurrentMetricData.html
        
        Args:
            queue_ids: List of queue IDs to get metrics for
        
        Returns:
            Dictionary with metric data:
            - MetricResults: List of results, one per queue
              Each result contains:
              - Dimensions: Queue info (QueueId, QueueName)
              - Collections: List of metrics with values
        
        Raises:
            ConnectAPIException: If API call fails
        
        Example:
            metrics = client.get_current_metric_data(['queue-1', 'queue-2'])
            for result in metrics['MetricResults']:
                queue_name = result['Dimensions']['Queue']['Name']
                for collection in result['Collections']:
                    if collection['Metric']['Name'] == 'CONTACTS_IN_QUEUE':
                        count = collection['Value']
        """
        logger.info(f"Getting current metrics for {len(queue_ids)} queue(s)")
        
        try:
            # Define which metrics we want
            # CONTACTS_IN_QUEUE = number of contacts waiting in queue
            current_metrics = [
                {
                    'Name': 'CONTACTS_IN_QUEUE',
                    'Unit': 'COUNT'
                }
            ]
            
            # Build filters for the queues we want
            filters = {
                'Queues': queue_ids,
                'Channels': ['VOICE']  # We're only interested in voice calls for now
            }
            
            # Add groupings to ensure we get queue IDs in the response
            groupings = ['QUEUE']
            
            # Make API call
            response = self.client.get_current_metric_data(
                InstanceId=self.instance_id,
                Filters=filters,
                Groupings=groupings,
                CurrentMetrics=current_metrics
            )
            
            logger.info(f"✓ Retrieved metrics for {len(response.get('MetricResults', []))} queue(s)")
            
            return response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"AWS API error getting current metrics: {error_code} - {error_message}")
            
            if error_code == 'ResourceNotFoundException':
                raise ConnectAPIException(f"One or more queues not found")
            elif error_code == 'AccessDeniedException':
                raise AuthenticationException("Access denied. Check IAM permissions.")
            elif error_code == 'ThrottlingException':
                raise RateLimitException("API rate limit exceeded. Please retry later.")
            else:
                raise ConnectAPIException(f"Error getting current metrics: {error_message}")
        
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            raise ConnectAPIException(f"AWS SDK error: {e}")


# ============================================
# Custom Exception Classes
# ============================================

class ConnectAPIException(Exception):
    """Base exception for Amazon Connect API errors."""
    pass


class AgentNotFoundException(ConnectAPIException):
    """Raised when an agent username is not found."""
    pass


class InvalidInstanceException(ConnectAPIException):
    """Raised when the Amazon Connect instance ID is invalid."""
    pass


class AuthenticationException(ConnectAPIException):
    """Raised when AWS authentication fails or permissions are insufficient."""
    pass


class RateLimitException(ConnectAPIException):
    """Raised when API rate limits are exceeded."""
    pass
