"""
Flask Routes - Web Endpoints

This module defines all the web routes (URLs) for the application.
Routes connect HTTP requests to business logic and return responses.
"""

import logging
from flask import render_template, request, session, jsonify, redirect, url_for
from app.services.agent_service import create_agent_service
from app.services.queue_service import create_queue_service
from app.clients.connect_client import AgentNotFoundException, ConnectAPIException

# Set up logging
logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all routes with the Flask application."""
    
    @app.route('/')
    def index():
        """Home page route - shows login form or detects embedded mode."""
        logger.info("Index page accessed")
        
        # Check if agent is already logged in
        if 'agent_username' in session:
            logger.info(f"Agent already logged in: {session['agent_username']}")
            return redirect(url_for('queue_view'))
        
        # Pass Connect instance URL to template for Streams API initialization
        from config.settings import Config
        return render_template('index.html', connect_instance_url=Config.CONNECT_INSTANCE_URL)
    
    
    @app.route('/agent/login', methods=['POST'])
    def agent_login():
        """Handle manual agent login from form submission."""
        logger.info("=" * 50)
        logger.info("MANUAL AGENT LOGIN ATTEMPT")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request is_json: {request.is_json}")
        
        try:
            # Get username from request (support both JSON and form data)
            if request.is_json:
                data = request.get_json()
                username = data.get('username', '').strip()
                logger.info(f"Received JSON data: {data}")
            else:
                username = request.form.get('username', '').strip()
                logger.info(f"Received form data: {dict(request.form)}")
            
            if not username:
                logger.warning("Login attempt with empty username")
                return jsonify({
                    'success': False,
                    'error': 'Username is required'
                }), 400
            
            logger.info(f"Attempting login for username: {username}")
            
            # Create agent service
            agent_service = create_agent_service()
            
            # Get agent information
            agent = agent_service.get_agent_by_username(username, detection_mode='manual')
            
            # Store in session
            session['agent_username'] = agent.username
            session['agent_id'] = agent.user_id  # Store agent ID for metrics
            session['detection_mode'] = 'manual'
            session['queue_ids'] = agent.assigned_queue_ids
            session['routing_profile_name'] = agent.routing_profile_name
            
            logger.info(f"✓ Agent logged in successfully: {username}")
            logger.info(f"Session data: agent_username={session.get('agent_username')}, detection_mode={session.get('detection_mode')}")
            logger.info(f"Session cookie config: SameSite={app.config.get('SESSION_COOKIE_SAMESITE')}, Secure={app.config.get('SESSION_COOKIE_SECURE')}")
            logger.info("=" * 50)
            
            # Return success response
            return jsonify({
                'success': True,
                'agent': {
                    'username': agent.username,
                    'routing_profile': agent.routing_profile_name,
                    'queue_count': len(agent.assigned_queue_ids)
                }
            })
            
        except AgentNotFoundException as e:
            logger.error(f"Agent not found: {e}")
            return jsonify({
                'success': False,
                'error': 'Agent not found. Please check your username.'
            }), 404
            
        except ConnectAPIException as e:
            logger.error(f"API error during login: {e}")
            return jsonify({
                'success': False,
                'error': 'Unable to connect to Amazon Connect. Please try again.'
            }), 500
            
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred. Please try again.'
            }), 500
    
    
    @app.route('/agent/auto-login', methods=['POST'])
    def agent_auto_login():
        """Handle automatic agent login from Streams API."""
        logger.info("Automatic agent login attempt (Streams API)")
        
        try:
            # Get username from request
            data = request.get_json()
            username = data.get('username', '').strip()
            
            if not username:
                logger.warning("Auto-login attempt with empty username")
                return jsonify({
                    'success': False,
                    'error': 'Username is required'
                }), 400
            
            logger.info(f"Attempting auto-login for username: {username}")
            
            # Create agent service
            agent_service = create_agent_service()
            
            # Get agent information
            agent = agent_service.get_agent_by_username(username, detection_mode='automatic')
            
            # Store in session
            session['agent_username'] = agent.username
            session['agent_id'] = agent.user_id  # Store agent ID for metrics
            session['detection_mode'] = 'automatic'
            session['queue_ids'] = agent.assigned_queue_ids
            session['routing_profile_name'] = agent.routing_profile_name
            
            logger.info(f"✓ Agent auto-logged in successfully: {username}")
            
            # Return success response
            return jsonify({
                'success': True,
                'agent': {
                    'username': agent.username,
                    'routing_profile': agent.routing_profile_name,
                    'queue_count': len(agent.assigned_queue_ids)
                }
            })
            
        except AgentNotFoundException as e:
            logger.error(f"Agent not found during auto-login: {e}")
            return jsonify({
                'success': False,
                'error': 'Agent not found in Amazon Connect.',
                'fallback_to_manual': True
            }), 404
            
        except ConnectAPIException as e:
            logger.error(f"API error during auto-login: {e}")
            return jsonify({
                'success': False,
                'error': 'Unable to connect to Amazon Connect.',
                'fallback_to_manual': True
            }), 500
            
        except Exception as e:
            logger.error(f"Unexpected error during auto-login: {e}")
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred.',
                'fallback_to_manual': True
            }), 500
    
    
    @app.route('/agent/queues')
    def queue_view():
        """Display agent's queue view with call counts."""
        logger.info("=" * 50)
        logger.info("QUEUE VIEW PAGE ACCESSED")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request cookies: {dict(request.cookies)}")
        logger.info(f"Session data: {dict(session)}")
        logger.info(f"Agent username in session: {session.get('agent_username')}")
        logger.info(f"Session cookie name: {app.config.get('SESSION_COOKIE_NAME', 'session')}")
        
        # Check if agent is logged in
        if 'agent_username' not in session:
            logger.warning("Queue view accessed without login - redirecting to index")
            logger.warning(f"Session is empty or missing agent_username")
            logger.warning(f"Available cookies: {list(request.cookies.keys())}")
            logger.info("=" * 50)
            return redirect(url_for('index'))
        
        username = session['agent_username']
        detection_mode = session.get('detection_mode', 'manual')
        queue_ids = session.get('queue_ids', [])
        routing_profile_name = session.get('routing_profile_name', 'Unknown')
        agent_id = session.get('agent_id')  # Get agent_id from session
        
        logger.info(f"Loading queue view for agent: {username} (ID: {agent_id})")
        
        try:
            # Get queue metrics with agent-specific data
            queue_service = create_queue_service()
            queue_metrics = queue_service.get_queue_metrics(queue_ids, agent_id=agent_id)
            
            # Get agent performance summary
            agent_performance = queue_service.get_agent_performance_summary(agent_id)
            
            logger.info(f"✓ Retrieved metrics for {len(queue_metrics)} queue(s)")
            
            # Render template with data
            return render_template(
                'queue_view.html',
                agent_username=username,
                detection_mode=detection_mode,
                routing_profile=routing_profile_name,
                queues=queue_metrics,
                total_contacts=sum(q.contacts_in_queue for q in queue_metrics if not q.error),
                agent_performance=agent_performance
            )
            
        except Exception as e:
            logger.error(f"Error loading queue view: {e}")
            # Render template with error
            return render_template(
                'queue_view.html',
                agent_username=username,
                detection_mode=detection_mode,
                routing_profile=routing_profile_name,
                queues=[],
                total_contacts=0,
                error="Unable to load queue metrics. Please try refreshing."
            )
    
    
    @app.route('/agent/queues/refresh', methods=['POST'])
    def refresh_queues():
        """Refresh queue metrics without reloading the page."""
        logger.info("Queue refresh requested")
        
        # Check if agent is logged in
        if 'agent_username' not in session:
            logger.warning("Refresh attempted without login")
            return jsonify({
                'success': False,
                'error': 'Not logged in'
            }), 401
        
        username = session['agent_username']
        queue_ids = session.get('queue_ids', [])
        agent_id = session.get('agent_id')
        
        logger.info(f"Refreshing queues for agent: {username} (ID: {agent_id})")
        
        try:
            # Get updated queue metrics with agent-specific data
            queue_service = create_queue_service()
            queue_metrics = queue_service.get_queue_metrics(queue_ids, agent_id=agent_id)
            
            # Get agent performance summary
            agent_performance = queue_service.get_agent_performance_summary(agent_id)
            
            logger.info(f"✓ Refreshed metrics for {len(queue_metrics)} queue(s)")
            
            # Convert to JSON-friendly format
            queues_data = [
                {
                    'queue_id': q.queue_id,
                    'queue_name': q.queue_name,
                    'contacts_in_queue': q.contacts_in_queue,
                    'calls_handled': q.calls_handled,
                    'calls_transferred_out': q.calls_transferred_out,
                    'available_agents': q.available_agents,
                    'non_productive_agents': q.non_productive_agents,
                    'error': q.error
                }
                for q in queue_metrics
            ]
            
            return jsonify({
                'success': True,
                'queues': queues_data,
                'agent_performance': agent_performance
            })
            
        except Exception as e:
            logger.error(f"Error refreshing queues: {e}")
            return jsonify({
                'success': False,
                'error': 'Unable to refresh queue metrics. Please try again.'
            }), 500
    
    
    @app.route('/agent/logout', methods=['GET', 'POST'])
    def agent_logout():
        """Log out the agent and clear session."""
        username = session.get('agent_username', 'Unknown')
        logger.info(f"Agent logout: {username}")
        
        # Clear session
        session.clear()
        
        logger.info("✓ Session cleared")
        
        # If it's a GET request (link click), redirect to home
        if request.method == 'GET':
            return redirect(url_for('index'))
        
        # If it's a POST request (AJAX), return JSON
        return jsonify({
            'success': True
        })
    
    
    @app.route('/debug/session')
    def debug_session():
        """Debug endpoint to check session and cookie status."""
        return jsonify({
            'session_data': dict(session),
            'cookies': dict(request.cookies),
            'headers': dict(request.headers),
            'session_cookie_name': app.config.get('SESSION_COOKIE_NAME', 'session'),
            'session_cookie_config': {
                'samesite': app.config.get('SESSION_COOKIE_SAMESITE'),
                'secure': app.config.get('SESSION_COOKIE_SECURE'),
                'httponly': app.config.get('SESSION_COOKIE_HTTPONLY')
            }
        })
