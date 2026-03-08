"""
Agent Service - Business Logic Layer

This module provides high-level business logic for agent operations.
It orchestrates multiple API calls to provide complete agent information.

Key Concepts for Beginners:
- Service Layer: Business logic that sits between API clients and web routes
- Dataclass: A Python class that primarily stores data (like a structured dictionary)
- Orchestration: Coordinating multiple API calls to accomplish a task
- Dual-Mode: Supporting both automatic (Streams API) and manual (login form) detection

Why This Matters:
The service layer simplifies complex operations. Instead of making multiple API calls
in your web routes, you call one service method that handles everything.

Example:
    Instead of:
        1. Search for user
        2. Get user details
        3. Get routing profile
        4. Extract queue IDs
    
    You just call:
        agent = agent_service.get_agent_by_username('john.doe')
        # Returns complete agent info with queues!
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from app.clients.connect_client import (
    ConnectClient,
    AgentNotFoundException,
    ConnectAPIException
)

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """
    Data class representing an Amazon Connect agent.
    
    This is a structured way to store agent information. Think of it like
    a custom dictionary with predefined fields.
    
    Attributes:
        user_id: Amazon Connect user ID (UUID)
        username: Agent's username (what they log in with)
        routing_profile_id: ID of their routing profile
        routing_profile_name: Human-readable name of routing profile
        assigned_queue_ids: List of queue IDs they handle
        detection_mode: How the agent was identified ('automatic' or 'manual')
    
    Example:
        agent = Agent(
            user_id='abc-123',
            username='john.doe',
            routing_profile_id='profile-456',
            routing_profile_name='Basic Routing Profile',
            assigned_queue_ids=['queue-1', 'queue-2'],
            detection_mode='automatic'
        )
        
        print(agent.username)  # 'john.doe'
        print(len(agent.assigned_queue_ids))  # 2
    """
    user_id: str
    username: str
    routing_profile_id: str
    routing_profile_name: str
    assigned_queue_ids: List[str]
    detection_mode: str  # 'automatic' or 'manual'


class AgentService:
    """
    Service class for agent-related business operations.
    
    This class provides high-level methods for working with agents.
    It uses ConnectClient to make API calls and orchestrates multiple
    calls to provide complete information.
    
    Supports dual-mode operation:
    - Automatic: Agent detected via Streams API (embedded mode)
    - Manual: Agent enters username (standalone mode)
    """
    
    def __init__(self, connect_client: Optional[ConnectClient] = None):
        """
        Initialize the Agent Service.
        
        Args:
            connect_client: Optional ConnectClient instance. 
                          If not provided, creates a new one.
        
        Example:
            # Use default client
            service = AgentService()
            
            # Or provide your own client
            client = ConnectClient(region_name='us-west-2')
            service = AgentService(connect_client=client)
        """
        # Use provided client or create a new one
        self.connect_client = connect_client or ConnectClient()
        logger.info("AgentService initialized")
    
    def get_agent_by_username(
        self, 
        username: str, 
        detection_mode: str = 'manual'
    ) -> Agent:
        """
        Get complete agent information by username.
        
        This is the main method you'll use. It orchestrates multiple API calls
        to gather all information about an agent:
        1. Search for user by username
        2. Get user details (including routing profile ID)
        3. Get routing profile details (name)
        4. List queues in routing profile
        
        Args:
            username: The agent's username
            detection_mode: How the agent was identified
                          - 'automatic': Detected via Streams API (embedded)
                          - 'manual': Entered by user (standalone)
        
        Returns:
            Agent object with complete information
        
        Raises:
            AgentNotFoundException: If username not found
            ConnectAPIException: If any API call fails
        
        Example:
            service = AgentService()
            
            # Automatic detection (from Streams API)
            agent = service.get_agent_by_username('john.doe', 'automatic')
            
            # Manual entry (from login form)
            agent = service.get_agent_by_username('jane.smith', 'manual')
            
            # Use the agent data
            print(f"Agent: {agent.username}")
            print(f"Routing Profile: {agent.routing_profile_name}")
            print(f"Handles {len(agent.assigned_queue_ids)} queues")
        """
        logger.info(f"Getting agent info for username: {username} (mode: {detection_mode})")
        
        try:
            # Step 1: Search for user by username
            logger.info("Step 1: Searching for user...")
            users = self.connect_client.search_users(username)
            
            if not users:
                raise AgentNotFoundException(f"No agent found with username: {username}")
            
            # Take the first matching user
            user_data = users[0]
            
            # Log the user data structure to help debug
            logger.info(f"User data keys: {list(user_data.keys())}")
            
            # Try different possible field names for user ID
            user_id = user_data.get('Id') or user_data.get('UserId') or user_data.get('user_id')
            
            if not user_id:
                logger.error(f"Could not find user ID in response. Available fields: {list(user_data.keys())}")
                raise ConnectAPIException(f"User ID not found in API response")
            
            logger.info(f"✓ Found user: {user_id}")
            
            # Step 2: Get detailed user information
            logger.info("Step 2: Getting user details...")
            user = self.connect_client.describe_user(user_id)
            routing_profile_id = user['RoutingProfileId']
            logger.info(f"✓ Routing Profile ID: {routing_profile_id}")
            
            # Step 3: Get routing profile details
            logger.info("Step 3: Getting routing profile...")
            routing_profile = self.connect_client.describe_routing_profile(routing_profile_id)
            routing_profile_name = routing_profile['Name']
            logger.info(f"✓ Routing Profile: {routing_profile_name}")
            
            # Step 4: Get queues assigned to routing profile
            logger.info("Step 4: Getting assigned queues...")
            queue_configs = self.connect_client.list_routing_profile_queues(routing_profile_id)
            
            # Extract queue IDs from the queue configurations
            assigned_queue_ids = [config['QueueId'] for config in queue_configs]
            logger.info(f"✓ Found {len(assigned_queue_ids)} assigned queue(s)")
            
            # Create and return Agent object
            agent = Agent(
                user_id=user_id,
                username=username,
                routing_profile_id=routing_profile_id,
                routing_profile_name=routing_profile_name,
                assigned_queue_ids=assigned_queue_ids,
                detection_mode=detection_mode
            )
            
            logger.info(f"✓ Successfully retrieved agent info for: {username}")
            return agent
            
        except AgentNotFoundException:
            # Re-raise agent not found errors
            logger.error(f"Agent not found: {username}")
            raise
            
        except ConnectAPIException as e:
            # Log and re-raise API errors
            logger.error(f"API error getting agent info: {e}")
            raise
            
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error getting agent info: {e}")
            raise ConnectAPIException(f"Failed to get agent info: {e}")
    
    def validate_agent_exists(self, username: str) -> bool:
        """
        Check if an agent exists without retrieving full details.
        
        This is a lightweight check - just searches for the username
        without making additional API calls.
        
        Args:
            username: The agent's username to validate
        
        Returns:
            True if agent exists, False otherwise
        
        Example:
            service = AgentService()
            
            if service.validate_agent_exists('john.doe'):
                print("Agent exists!")
            else:
                print("Agent not found")
        """
        logger.info(f"Validating agent exists: {username}")
        
        try:
            users = self.connect_client.search_users(username)
            exists = len(users) > 0
            
            if exists:
                logger.info(f"✓ Agent exists: {username}")
            else:
                logger.info(f"✗ Agent not found: {username}")
            
            return exists
            
        except AgentNotFoundException:
            logger.info(f"✗ Agent not found: {username}")
            return False
            
        except ConnectAPIException as e:
            logger.error(f"Error validating agent: {e}")
            # On API error, we can't confirm existence
            return False
    
    def get_agent_routing_profile_name(self, username: str) -> str:
        """
        Get just the routing profile name for an agent.
        
        This is a convenience method when you only need the routing profile name
        and don't want to retrieve all agent information.
        
        Args:
            username: The agent's username
        
        Returns:
            Routing profile name
        
        Raises:
            AgentNotFoundException: If username not found
            ConnectAPIException: If any API call fails
        
        Example:
            service = AgentService()
            profile_name = service.get_agent_routing_profile_name('john.doe')
            print(f"Routing Profile: {profile_name}")
        """
        logger.info(f"Getting routing profile name for: {username}")
        
        try:
            # Search for user
            users = self.connect_client.search_users(username)
            if not users:
                raise AgentNotFoundException(f"No agent found with username: {username}")
            
            user_id = users[0]['UserId']
            
            # Get user details
            user = self.connect_client.describe_user(user_id)
            routing_profile_id = user['RoutingProfileId']
            
            # Get routing profile
            routing_profile = self.connect_client.describe_routing_profile(routing_profile_id)
            routing_profile_name = routing_profile['Name']
            
            logger.info(f"✓ Routing profile for {username}: {routing_profile_name}")
            return routing_profile_name
            
        except (AgentNotFoundException, ConnectAPIException):
            raise
        except Exception as e:
            logger.error(f"Error getting routing profile name: {e}")
            raise ConnectAPIException(f"Failed to get routing profile name: {e}")
    
    def get_agent_queue_count(self, username: str) -> int:
        """
        Get the number of queues assigned to an agent.
        
        This is a convenience method when you only need to know how many
        queues an agent handles, not the full details.
        
        Args:
            username: The agent's username
        
        Returns:
            Number of queues assigned to the agent
        
        Raises:
            AgentNotFoundException: If username not found
            ConnectAPIException: If any API call fails
        
        Example:
            service = AgentService()
            count = service.get_agent_queue_count('john.doe')
            print(f"Agent handles {count} queues")
        """
        logger.info(f"Getting queue count for: {username}")
        
        try:
            # Get full agent info
            agent = self.get_agent_by_username(username)
            
            # Return queue count
            count = len(agent.assigned_queue_ids)
            logger.info(f"✓ Agent {username} handles {count} queue(s)")
            
            return count
            
        except (AgentNotFoundException, ConnectAPIException):
            raise
        except Exception as e:
            logger.error(f"Error getting queue count: {e}")
            raise ConnectAPIException(f"Failed to get queue count: {e}")


# ============================================
# Helper Functions
# ============================================

def create_agent_service() -> AgentService:
    """
    Factory function to create an AgentService instance.
    
    This is a convenience function that creates a service with default settings.
    Use this in your Flask routes for consistency.
    
    Returns:
        Configured AgentService instance
    
    Example:
        # In your Flask route
        from app.services.agent_service import create_agent_service
        
        @app.route('/agent/<username>')
        def get_agent(username):
            service = create_agent_service()
            agent = service.get_agent_by_username(username)
            return jsonify({
                'username': agent.username,
                'routing_profile': agent.routing_profile_name,
                'queue_count': len(agent.assigned_queue_ids)
            })
    """
    return AgentService()
