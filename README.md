# Amazon Connect Third-Party App Workshop

Welcome to the Amazon Connect Third-Party App Workshop! This is a hands-on learning experience that teaches you how to build web applications that integrate with Amazon Connect and can be embedded directly in the agent workspace.

## 🎯 What You'll Build

An agent-focused web application that:
- Shows agents their assigned queues
- Displays how many calls are waiting in each queue
- Automatically detects the logged-in agent when embedded in Amazon Connect
- Works both as a standalone app (for development) and embedded in Amazon Connect

## 🏗️ Project Structure

```
amazon-connect-workshop/
├── app/                    # Main application code
│   ├── clients/           # Amazon Connect API client
│   ├── services/          # Business logic (agent & queue services)
│   ├── static/            # CSS, JavaScript, images
│   ├── templates/         # HTML templates
│   └── routes.py          # Web routes (URLs)
├── config/                # Configuration management
│   └── settings.py        # Loads settings from .env file
├── tests/                 # Test files
├── docs/                  # Workshop documentation
├── requirements.txt       # Python dependencies
├── .env.example          # Configuration template
└── README.md             # This file!
```

## 📚 Learning Path

This workshop is divided into 8 progressive phases:

1. **Phase 1**: Environment Setup & SDK Installation
2. **Phase 2**: Iframe Compatibility Setup
3. **Phase 3**: Amazon Connect Streams API Integration
4. **Phase 4**: Mode Detection & Agent Identification
5. **Phase 5**: Routing Profile & Queue Retrieval
6. **Phase 6**: Queue Metrics Retrieval
7. **Phase 7**: Web Interface Development
8. **Phase 8**: Third-Party App Configuration in Amazon Connect

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- AWS Account with Amazon Connect instance
- AWS credentials configured (AWS CLI or environment variables)
- Basic understanding of Python (we'll explain as we go!)

### Setup Steps

1. **Clone or download this project**

2. **Create a virtual environment** (isolated Python environment)
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure your environment**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in your Amazon Connect details

6. **Run the application** (once we build it!)
   ```bash
   python run.py
   ```

## 🔑 Configuration

You'll need to configure these settings in your `.env` file:

- `AWS_REGION`: Your AWS region (e.g., us-east-1)
- `CONNECT_INSTANCE_ID`: Your Amazon Connect instance ID (UUID format)
- `CONNECT_INSTANCE_URL`: Your Amazon Connect instance URL
- `FLASK_SECRET_KEY`: A random secret key for sessions
- `ALLOWED_ORIGINS`: Domains allowed to embed your app

See `.env.example` for detailed explanations of each setting.

## 🎓 Key Concepts You'll Learn

### Amazon Connect SDK (boto3)
- How to search for agents
- How to retrieve routing profiles
- How to get queue metrics
- How to handle API errors

### Amazon Connect Streams API
- How to detect the logged-in agent automatically
- How to integrate with the Contact Control Panel (CCP)
- How to handle embedded vs standalone modes

### Web Development
- Building web pages with Flask (Python web framework)
- Creating dynamic interfaces with JavaScript
- Styling with CSS
- Handling user sessions

### Iframe Embedding
- Configuring security headers (CORS, CSP)
- Making your app work inside Amazon Connect
- Handling cross-origin requests

## 🛠️ Technology Stack

- **Backend**: Python 3.8+ with Flask
- **AWS SDK**: boto3 (Amazon Connect Python SDK)
- **Frontend**: HTML, CSS, vanilla JavaScript
- **Streams API**: Amazon Connect Streams JavaScript library
- **Testing**: pytest, hypothesis (property-based testing)

## 📖 Documentation

Detailed phase-by-phase guides will be available in the `docs/` directory:

- `SETUP.md` - Detailed setup instructions
- `PHASE_1.md` - SDK installation guide
- `PHASE_2.md` - Iframe compatibility setup
- `PHASE_3.md` - Streams API integration
- `PHASE_4.md` - Agent identification
- `PHASE_5.md` - Routing profile retrieval
- `PHASE_6.md` - Queue metrics
- `PHASE_7.md` - Web interface
- `PHASE_8.md` - Third-party app configuration
- `TROUBLESHOOTING.md` - Common issues and solutions

## 🎨 Future Enhancement Ideas

Once you complete the workshop, try these enhancements:

**Beginner**:
- Add color coding for high call volumes
- Display last refresh timestamp
- Show total calls across all queues

**Intermediate**:
- Implement auto-refresh every 30 seconds
- Add charts for queue volumes
- Display additional metrics (oldest contact age, average wait time)

**Advanced**:
- Build supervisor view for multiple agents
- Add historical trend data
- Implement real-time updates with WebSocket
- Integrate with other Streams API features

## 🤝 Support

If you get stuck:
1. Check `docs/TROUBLESHOOTING.md`
2. Review the phase guides in `docs/`
3. Look at the inline code comments
4. Check AWS documentation for Amazon Connect

## 📝 License

This workshop is for educational purposes.

## 🎉 Let's Get Started!

Ready to build your first Amazon Connect third-party app? Let's go! 🚀
