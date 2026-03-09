# Repository Structure

This document explains the organization of the Connect Queue Monitor repository.

## Directory Layout

```
connect-queue-monitor/
├── app/                          # Application code
│   ├── __init__.py              # Flask app initialization and configuration
│   ├── routes.py                # HTTP endpoints (login, logout, queue-view, refresh)
│   ├── clients/                 # AWS API clients
│   │   ├── __init__.py
│   │   └── connect_client.py   # Amazon Connect API wrapper
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── agent_service.py    # Agent operations (search, get by username)
│   │   └── queue_service.py    # Queue metrics and performance calculations
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── index.html          # Login page
│   │   └── queue_view.html     # Queue dashboard with metrics
│   └── static/                  # Static assets
│       ├── css/
│       │   └── styles.css      # Application styles with branding
│       ├── js/
│       │   ├── mode-detector.js    # Detect embedded vs standalone mode
│       │   ├── streams.js          # Amazon Connect Streams API integration
│       │   └── app.js              # Main application JavaScript
│       └── images/
│           └── logo.png            # Organization logo
│
├── config/                      # Configuration files
│   ├── __init__.py
│   └── settings.py             # Application settings and environment variables
│
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md         # System architecture and design decisions
│   ├── DEPLOYMENT.md           # Step-by-step deployment guide
│   ├── API_REFERENCE.md        # Complete API endpoint documentation
│   ├── TROUBLESHOOTING.md      # Common issues and solutions
│   ├── COST_ANALYSIS.md        # Detailed cost breakdown
│   ├── LAMBDA_ALTERNATIVE.md   # How to migrate to serverless
│   └── REPOSITORY_STRUCTURE.md # This file
│
├── scripts/                     # Helper scripts
│   └── create_deployment_package.sh  # Create deployment zip file
│
├── .ebextensions/              # Elastic Beanstalk extensions
│   └── python.config           # Python environment configuration
│
├── .platform/                  # Platform-specific configuration
│   └── nginx/
│       └── conf.d/
│           └── custom.conf     # Nginx custom configuration
│
├── .kiro/                      # Kiro AI specs (development artifacts)
│   └── specs/
│       ├── amazon-connect-third-party-app/
│       │   ├── requirements.md
│       │   ├── design.md
│       │   └── tasks.md
│       └── agent-dashboard-enhancements/
│           ├── requirements.md
│           ├── design.md
│           ├── tasks.md
│           └── .config.kiro
│
├── requirements.txt            # Python dependencies
├── run.py                      # Application entry point
├── Procfile                    # Process file for Elastic Beanstalk
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore patterns
├── LICENSE                     # MIT License
└── README.md                   # Project overview and quick start
```

## Key Files Explained

### Application Core

**`run.py`**
- Entry point for the application
- Starts Flask development server
- Configures host and port

**`app/__init__.py`**
- Creates Flask application instance
- Configures session management
- Sets up CORS for Amazon Connect embedding
- Adds security headers (CSP, X-Frame-Options)

**`app/routes.py`**
- Defines HTTP endpoints
- Handles authentication and session management
- Renders templates with data from services

### Business Logic

**`app/services/agent_service.py`**
- Agent-related operations
- Searches for agents by username
- Retrieves agent details from Amazon Connect

**`app/services/queue_service.py`**
- Queue metrics retrieval
- Performance summary calculations
- Combines real-time and historical data
- Handles timezone conversions

### AWS Integration

**`app/clients/connect_client.py`**
- Wrapper around boto3 Connect client
- Provides methods for:
  - SearchUsers
  - DescribeRoutingProfile
  - GetCurrentMetricData
  - GetMetricDataV2

### Frontend

**`app/templates/index.html`**
- Login page
- Mode detection (embedded vs standalone)
- Streams API initialization

**`app/templates/queue_view.html`**
- Queue metrics table
- Performance summary cards
- Auto-refresh functionality
- Logout button

**`app/static/css/styles.css`**
- Professional styling with brand colors
- Responsive design for 400-800px panels
- Color-coded status badges
- Gradient headers

**`app/static/js/mode-detector.js`**
- Detects if app is embedded in Amazon Connect
- Checks for parent window and Streams API

**`app/static/js/streams.js`**
- Initializes Amazon Connect Streams API
- Retrieves agent information automatically
- Handles CCP (Contact Control Panel) integration

**`app/static/js/app.js`**
- Auto-refresh timer (15 seconds)
- Updates queue table and performance summary
- Handles tab visibility (pauses when hidden)

### Configuration

**`config/settings.py`**
- Loads environment variables
- Provides configuration constants
- Validates required settings

**`.env.example`**
- Template for environment variables
- Documents required configuration

### Deployment

**`.ebextensions/python.config`**
- Elastic Beanstalk Python configuration
- Sets Python version and WSGI path

**`.platform/nginx/conf.d/custom.conf`**
- Nginx configuration for Elastic Beanstalk
- Proxy settings and timeouts

**`Procfile`**
- Defines process type for Elastic Beanstalk
- Specifies Gunicorn as WSGI server

**`scripts/create_deployment_package.sh`**
- Helper script to create deployment zip
- Excludes unnecessary files
- Includes all required configuration

### Documentation

**`docs/ARCHITECTURE.md`**
- System architecture overview
- Component descriptions
- Data flow diagrams
- Technology stack explanation

**`docs/DEPLOYMENT.md`**
- Step-by-step deployment guide
- Environment setup instructions
- CloudFront configuration
- Amazon Connect integration

**`docs/API_REFERENCE.md`**
- Complete API endpoint documentation
- Request/response formats
- Error handling
- Testing examples

**`docs/TROUBLESHOOTING.md`**
- Common issues and solutions
- Debugging tips
- AWS API troubleshooting
- Performance optimization

**`docs/COST_ANALYSIS.md`**
- Detailed cost breakdown
- Cost optimization strategies
- Comparison with alternatives
- Scaling considerations

**`docs/LAMBDA_ALTERNATIVE.md`**
- How to migrate to Lambda + API Gateway
- Architecture comparison
- Step-by-step migration guide
- Cost comparison

## File Naming Conventions

### Python Files
- **Snake case**: `agent_service.py`, `connect_client.py`
- **Descriptive names**: Clearly indicate purpose
- **`__init__.py`**: Package initialization files

### HTML Templates
- **Lowercase with underscores**: `queue_view.html`
- **Descriptive names**: Indicate page purpose

### JavaScript Files
- **Kebab case**: `mode-detector.js`, `app.js`
- **Descriptive names**: Indicate functionality

### CSS Files
- **Lowercase**: `styles.css`
- **Singular form**: One main stylesheet

### Documentation
- **UPPERCASE.md**: `README.md`, `LICENSE`
- **Title case**: `ARCHITECTURE.md`, `DEPLOYMENT.md`
- **Descriptive names**: Clear indication of content

## Dependencies

### Python Packages (requirements.txt)

```
Flask==2.3.3              # Web framework
Flask-CORS==4.0.0         # Cross-origin resource sharing
boto3==1.28.25            # AWS SDK for Python
python-dotenv==1.0.0      # Environment variable management
gunicorn==21.2.0          # WSGI HTTP server
pytz==2023.3              # Timezone handling
```

### External Services

- **Amazon Connect**: Contact center platform
- **AWS Elastic Beanstalk**: Application hosting
- **AWS CloudFront**: HTTPS and CDN
- **AWS IAM**: Authentication and authorization

## Development Artifacts

### `.kiro/specs/`
- Contains Kiro AI-generated specifications
- Documents requirements, design, and tasks
- Useful for understanding feature development history
- Not required for production deployment

## Excluded Files

The following files are excluded via `.gitignore`:

- **Python cache**: `__pycache__/`, `*.pyc`
- **Virtual environments**: `venv/`, `env/`
- **Environment variables**: `.env`
- **IDE files**: `.vscode/`, `.idea/`
- **Deployment packages**: `*.zip`
- **Logs**: `*.log`
- **OS files**: `.DS_Store`, `Thumbs.db`

## Repository Size

Approximate sizes:

- **Application code**: ~50 KB
- **Static assets**: ~100 KB (including logo)
- **Documentation**: ~200 KB
- **Configuration**: ~10 KB
- **Total (excluding dependencies)**: ~360 KB

## Version Control

### Git Workflow

1. **Main branch**: Production-ready code
2. **Feature branches**: `feature/feature-name`
3. **Bugfix branches**: `bugfix/bug-description`
4. **Release tags**: `v1.0.0`, `v1.1.0`, etc.

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example**:
```
feat: Add auto-refresh functionality

- Implement 15-second refresh timer
- Add pause/resume on tab visibility
- Update queue metrics and performance summary

Closes #123
```

## Maintenance

### Regular Tasks

1. **Update dependencies**: Monthly security updates
2. **Review logs**: Weekly CloudWatch log review
3. **Monitor costs**: Monthly AWS cost review
4. **Test functionality**: Weekly smoke tests
5. **Update documentation**: As features change

### Backup Strategy

1. **Code**: Stored in GitHub (primary backup)
2. **Configuration**: Documented in `.env.example`
3. **Deployment packages**: Created on-demand with script
4. **Documentation**: Version controlled in Git

## Additional Resources

- **GitHub Repository**: https://github.com/Sabiha-git-hub/connect-queue-monitor
- **Live Application**: https://dzh4oz4t3wz32.cloudfront.net
- **AWS Console**: https://console.aws.amazon.com/
- **Amazon Connect**: https://unt-sample-cicd-instance-sab-test.my.connect.aws

## Questions?

For questions about the repository structure:
1. Check the documentation in `docs/`
2. Review the code comments
3. Open an issue on GitHub
4. Contact the maintainers
