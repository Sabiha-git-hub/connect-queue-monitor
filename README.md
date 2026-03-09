# Amazon Connect Queue Monitor

A Flask-based web application that displays real-time queue metrics and agent performance data for Amazon Connect contact centers. Designed to be embedded in the Amazon Connect agent workspace or used as a standalone dashboard.

![Application Screenshot](docs/images/screenshot.png)

## Features

- **Real-Time Queue Metrics**: View contacts in queue, available agents, and agent status
- **Historical Performance Data**: Track calls handled, transfers, and average handle time
- **Personal Performance Summary**: See your individual metrics for the current day
- **Automatic Refresh**: Updates every 15 seconds to keep data current
- **Dual Mode Operation**: Works embedded in Amazon Connect or as standalone dashboard
- **Professional Branding**: Customizable with your organization's logo and colors
- **Secure Authentication**: Session-based authentication with secure cookies
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

## Quick Start

### Prerequisites

- Python 3.11 or higher
- AWS Account with Amazon Connect instance
- AWS credentials with Connect API permissions
- Git (for cloning the repository)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Sabiha-git-hub/connect-queue-monitor.git
   cd connect-queue-monitor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and Connect instance details
   ```

4. **Run the application**:
   ```bash
   python3 run.py
   ```

5. **Open in browser**:
   ```
   http://localhost:8080
   ```

### Production Deployment

**New to this project?** Start here:
- **[DEPLOYMENT_FROM_SCRATCH.md](DEPLOYMENT_FROM_SCRATCH.md)** - Complete step-by-step guide for deploying to a new AWS account and Connect instance (2-3 hours)
- **[QUICK_DEPLOYMENT_CHECKLIST.md](QUICK_DEPLOYMENT_CHECKLIST.md)** - Quick reference checklist for experienced users

**Already familiar?** See:
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Detailed deployment documentation

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System architecture and design decisions
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Step-by-step deployment to AWS
- **[API Reference](docs/API_REFERENCE.md)** - Complete API endpoint documentation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Cost Analysis](docs/COST_ANALYSIS.md)** - Detailed cost breakdown and optimization
- **[Lambda Alternative](docs/LAMBDA_ALTERNATIVE.md)** - How to migrate to serverless architecture

## Project Structure

```
connect-queue-monitor/
├── app/                          # Application code
│   ├── __init__.py              # Flask app initialization
│   ├── routes.py                # HTTP endpoints
│   ├── clients/                 # AWS API clients
│   │   └── connect_client.py   # Amazon Connect API wrapper
│   ├── services/                # Business logic
│   │   ├── agent_service.py    # Agent operations
│   │   └── queue_service.py    # Queue metrics and performance
│   ├── templates/               # HTML templates
│   │   ├── index.html          # Login page
│   │   └── queue_view.html     # Queue dashboard
│   └── static/                  # Static assets
│       ├── css/                 # Stylesheets
│       ├── js/                  # JavaScript
│       └── images/              # Logo and images
├── config/                      # Configuration
│   └── settings.py             # App settings
├── docs/                        # Documentation
├── .ebextensions/              # Elastic Beanstalk config
├── .platform/                  # Nginx config
├── requirements.txt            # Python dependencies
├── run.py                      # Application entry point
└── README.md                   # This file
```

## Technology Stack

- **Backend**: Flask 2.3.3 (Python web framework)
- **AWS Services**: 
  - Amazon Connect (contact center)
  - Elastic Beanstalk (hosting)
  - CloudFront (HTTPS and CDN)
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Authentication**: Flask sessions with secure cookies
- **APIs**: AWS Connect API (boto3)

## Configuration

### Environment Variables

Required environment variables (set in `.env` for local, Elastic Beanstalk environment for production):

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_SESSION_TOKEN=your-session-token  # Optional, for temporary credentials

# Amazon Connect Configuration
CONNECT_INSTANCE_ID=your-instance-id
CONNECT_INSTANCE_URL=https://your-instance.my.connect.aws

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
PORT=8000  # Optional, defaults to 8000
```

### IAM Permissions

The application requires the following IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:SearchUsers",
        "connect:DescribeRoutingProfile",
        "connect:GetCurrentMetricData",
        "connect:GetMetricDataV2"
      ],
      "Resource": "*"
    }
  ]
}
```

## Usage

### Standalone Mode

1. Navigate to the application URL
2. Enter your Amazon Connect username
3. Click "Login"
4. View your assigned queues and performance metrics
5. Dashboard auto-refreshes every 15 seconds

### Embedded Mode (Amazon Connect)

1. Add the application as a third-party app in Amazon Connect:
   - Go to Amazon Connect admin panel
   - Routing → Third-party applications
   - Add application with CloudFront URL
   - Set "Contact scope" to "Cross contacts"

2. Agents will see the app in their workspace:
   - Automatically detects agent from Streams API
   - No manual login required
   - Stays visible across calls

## Metrics Explained

### Queue Metrics

- **Contacts in Queue**: Number of customers waiting (real-time)
- **Calls Handled**: Total calls handled today (historical, updates with delay)
- **Calls Transferred**: Total calls transferred today (historical, updates with delay)
- **Available Agents**: Agents ready to take calls (real-time)
- **Non-Productive**: Agents in custom status like "Busy" (real-time)
- **Status**: Queue status (Active/Inactive)

### Performance Summary

- **Calls Handled**: Your total calls handled today
- **Avg Handle Time**: Average time per call (talk + hold + after-call work)
- **Calls Transferred**: Your total calls transferred today

All metrics are calculated from midnight to current time in your Connect instance timezone.

## Cost Estimate

For a typical deployment with 50 agents:

- **Elastic Beanstalk**: $17/month (t3.micro instance + load balancer)
- **CloudFront**: $1/month (data transfer)
- **Amazon Connect API**: $19/month (15-second refresh interval)
- **Total**: ~$37/month

See [docs/COST_ANALYSIS.md](docs/COST_ANALYSIS.md) for detailed breakdown and optimization tips.

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_queue_service.py

# Run with coverage
python -m pytest --cov=app
```

### Code Style

The project follows PEP 8 style guidelines. Format code with:

```bash
# Install formatter
pip install black

# Format code
black app/
```

### Adding New Features

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run tests: `python -m pytest`
4. Commit changes: `git commit -m "Add your feature"`
5. Push to GitHub: `git push origin feature/your-feature`
6. Create a pull request

## Troubleshooting

Common issues and solutions:

- **Login fails**: Check username exists in Amazon Connect, verify AWS credentials
- **Metrics show zero**: Verify agent has queues assigned, check IAM permissions
- **Session expires**: Sessions last 24 hours, log in again
- **App doesn't load in Connect**: Check CSP headers, verify CORS configuration

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for complete troubleshooting guide.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:

- **Documentation**: Check the `docs/` directory
- **Issues**: Open an issue on GitHub
- **AWS Support**: For AWS-specific issues, contact AWS Support

## Acknowledgments

- Built for Amazon Connect contact centers
- Uses AWS Connect API and Streams API
- Deployed on AWS Elastic Beanstalk with CloudFront

## Roadmap

Future enhancements:

- [ ] Real-time notifications for queue thresholds
- [ ] Historical trend charts
- [ ] Export metrics to CSV
- [ ] Multi-language support
- [ ] Dark mode theme
- [ ] Mobile app version

## Authors

- **Sabiha** - Initial development

## Version History

- **1.0.0** (2024-03-10)
  - Initial release
  - Real-time queue metrics
  - Personal performance summary
  - Dual mode operation (embedded/standalone)
  - 15-second auto-refresh
  - Professional branding support

---

**Live Demo**: https://dzh4oz4t3wz32.cloudfront.net

**Repository**: https://github.com/Sabiha-git-hub/connect-queue-monitor
