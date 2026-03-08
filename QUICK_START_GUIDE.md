# Amazon Connect Queue Monitor - Quick Start Guide

## 🚀 Application URLs

### Local Access
- **Main URL**: http://localhost:8080
- Use this when accessing from the same computer running the app

### Network Access
- **Network URL**: http://192.168.1.242:8080
- Use this when accessing from other devices on your network (phones, tablets, other computers)

---

## 📋 How to Use

### Starting the Application

1. **Activate your virtual environment** (if not already active):
   ```bash
   source venv/bin/activate
   ```

2. **Start the Flask app**:
   ```bash
   python3 run.py
   ```

3. **Look for this message** in the terminal:
   ```
   * Running on http://127.0.0.1:8080
   * Running on http://192.168.1.242:8080
   ```

### Using the Application

#### Standalone Mode (Development/Testing)
1. Open your browser and go to: **http://localhost:8080**
2. Enter your Amazon Connect username (e.g., "Sabiha")
3. Click "Login"
4. You'll see:
   - Your routing profile name
   - All queues assigned to you
   - Current call count for each queue

#### Embedded Mode (Production)
- When embedded as a third-party app in Amazon Connect agent workspace
- Agent detection happens automatically via Streams API
- No login required - seamless experience

---

## 🔧 Configuration

### Current Setup
- **AWS Region**: us-east-1
- **Connect Instance ID**: 6091de37-993e-45c8-9637-e9e3a0af5b23
- **Connect Instance URL**: https://unt-sample-cicd-instance-sab-test.my.connect.aws
- **Port**: 8080

### AWS Credentials
Your app is currently using temporary AWS credentials stored in `.env`:
- These credentials expire after a few hours
- When they expire, you'll need to update them in the `.env` file

---

## 🛠️ Troubleshooting

### App Won't Start
- **Error: "Port 8080 is in use"**
  - Another app is using port 8080
  - Stop the other app or change the port in `run.py`

### Can't Login
- **Error: "Unable to connect to Amazon Connect"**
  - Check if AWS credentials in `.env` are still valid
  - Verify the Connect instance ID is correct
  - Make sure you have network connectivity

### Queues Not Showing
- Verify you're assigned to queues in your routing profile
- Check Amazon Connect console to confirm queue assignments
- Try refreshing the page

### Browser Shows Old Version
- Do a hard refresh: **Cmd + Shift + R** (Mac) or **Ctrl + Shift + R** (Windows)
- This clears cached JavaScript and CSS files

---

## 📱 Accessing from Mobile/Other Devices

1. Make sure your device is on the same WiFi network
2. Open browser and go to: **http://192.168.1.242:8080**
3. Login with your username
4. View your queues on the go!

---

## 🔒 Security Notes

### Development Mode
- Currently running in **DEBUG mode** - only use for development
- CORS is relaxed to allow localhost access
- Session cookies work without HTTPS

### For Production
- Set `FLASK_DEBUG=False` in `.env`
- Use a production WSGI server (Gunicorn or uWSGI)
- Enable HTTPS
- Use permanent AWS credentials or IAM roles
- Restrict CORS to your Connect instance domains only

---

## 📚 What This App Does

### Features
✅ Displays agent's assigned queues  
✅ Shows real-time call counts per queue  
✅ Dual-mode operation (embedded + standalone)  
✅ Automatic agent detection via Streams API  
✅ Manual login for testing  

### Technical Stack
- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **AWS SDK**: boto3
- **Amazon Connect**: Streams API + REST API

---

## 🎯 Next Steps

### To Embed in Amazon Connect
1. Deploy app to a public server (AWS EC2, Heroku, etc.)
2. Enable HTTPS
3. Add app URL to Amazon Connect third-party applications
4. Configure security settings in Amazon Connect console
5. Agents will see it automatically in their workspace

### To Customize
- Modify `app/templates/queue_view.html` for UI changes
- Update `app/static/css/styles.css` for styling
- Add new features in `app/routes.py`

---

## 📞 Support

### Useful AWS Documentation
- [Amazon Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/)
- [Amazon Connect Streams API](https://github.com/amazon-connect/amazon-connect-streams)
- [Third-Party Applications Guide](https://docs.aws.amazon.com/connect/latest/adminguide/3p-apps.html)

### Common Commands
```bash
# Start the app
python3 run.py

# Stop the app
Ctrl + C

# Check if port 8080 is in use
lsof -i :8080

# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate
```

---

**Last Updated**: March 8, 2026  
**Version**: 1.0  
**Status**: ✅ Working
