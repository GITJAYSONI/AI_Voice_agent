# ngrok Setup Guide for AI Voice Agent

## 🎯 What is ngrok?

ngrok is a tool that creates a secure tunnel from the public internet to your local development server. This is essential for testing Twilio webhooks locally.

---

## 📥 Installation

### Windows (PowerShell):
```powershell
# Using Chocolatey
choco install ngrok

# Or download from https://ngrok.com/download
# Extract and add to PATH
```

### Verify Installation:
```bash
ngrok version
```

---

## 🔑 Setup (One-time)

### 1. Create Account
Visit: https://dashboard.ngrok.com/signup

### 2. Get Auth Token
After signing up, copy your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken

### 3. Configure ngrok
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
```

---

## 🚀 Running Your AI Voice Agent with ngrok

### Step 1: Start Your FastAPI Server
```bash
# Navigate to project directory
cd c:\Users\jayso\OneDrive\Desktop\Ai-voice-agent

# Activate virtual environment (if using one)
.venv\Scripts\activate

# Start the server
python main.py
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000
```

### Step 2: Start ngrok (in a new terminal)
```bash
ngrok http 5000
```

You'll see:
```
ngrok                                                                           

Session Status                online
Account                       your-email@example.com
Version                       3.x.x
Region                        United States (us)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Important:** Copy the `Forwarding` URL (e.g., `https://abc123.ngrok.io`)

### Step 3: Configure Twilio
1. Go to: https://console.twilio.com/
2. Navigate to: Phone Numbers → Manage → Active Numbers
3. Click on your phone number
4. Scroll to "Voice Configuration"
5. Set "A CALL COMES IN" webhook to:
   ```
   https://abc123.ngrok.io/incoming-call
   ```
6. Set HTTP method to: `POST`
7. Click "Save"

### Step 4: Test!
Call your Twilio phone number and you should hear the AI greeting!

---

## 🔍 Debugging with ngrok Web Interface

### Access the Dashboard
Open in browser: http://localhost:4040

### Features:
- **Request Inspector:** See all HTTP requests in real-time
- **Replay Requests:** Resend requests for testing
- **Request Details:** View headers, body, response
- **Status Codes:** Check for errors

### Example: Viewing a Call
1. Make a test call
2. Open http://localhost:4040
3. You'll see:
   - POST to `/incoming-call`
   - WebSocket upgrade to `/media-stream`
   - All request/response data

---

## ⚠️ Important Notes

### Free Plan Limitations:
- ✅ HTTPS tunnel
- ✅ Web interface
- ✅ Request inspection
- ❌ URL changes every restart
- ❌ Limited to 40 connections/minute

### URL Changes:
Every time you restart ngrok, you get a new URL like:
- First run: `https://abc123.ngrok.io`
- Second run: `https://xyz789.ngrok.io`

**You must update Twilio webhook URL each time!**

### Solution: Paid Plan
- Get a static subdomain: `https://yourname.ngrok.io`
- Never changes, even after restart
- Cost: ~$8/month

---

## 🎯 Quick Commands Cheat Sheet

```bash
# Start ngrok on port 5000
ngrok http 5000

# Start with specific region
ngrok http 5000 --region us

# Start with custom subdomain (paid plan)
ngrok http 5000 --subdomain=myvoiceagent

# View ngrok config
ngrok config check

# View ngrok version
ngrok version
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "ngrok not found"
**Solution:** Add ngrok to PATH or use full path:
```bash
C:\path\to\ngrok.exe http 5000
```

### Issue 2: "Tunnel not found"
**Solution:** Make sure you've added your auth token:
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Issue 3: Twilio can't connect
**Solution:** 
- Check ngrok is running
- Verify URL in Twilio matches ngrok URL exactly
- Ensure your server is running on port 5000

### Issue 4: URL keeps changing
**Solution:** 
- Use a paid plan for static subdomain
- Or create a script to auto-update Twilio webhook

### Issue 5: "ERR_NGROK_108"
**Solution:** You've exceeded free plan limits. Wait or upgrade.

---

## 🔄 Development Workflow

### Terminal 1: Server
```bash
cd c:\Users\jayso\OneDrive\Desktop\Ai-voice-agent
python main.py
```

### Terminal 2: ngrok
```bash
ngrok http 5000
```

### Terminal 3: Development
```bash
# Make code changes
# Server auto-reloads (if using --reload flag)
# ngrok tunnel stays active
```

---

## 🚀 Production Deployment

**For production, you DON'T use ngrok!**

Instead:
1. Deploy to a cloud service (AWS, GCP, Azure, Heroku)
2. Get a real domain with SSL certificate
3. Point Twilio webhook to your production URL

### Example Production URLs:
```
https://api.yourcompany.com/incoming-call
wss://api.yourcompany.com/media-stream
```

ngrok is **only for local development and testing!**

---

## 📊 ngrok vs Production

| Feature | ngrok (Dev) | Production |
|---------|-------------|------------|
| Purpose | Local testing | Live service |
| URL | `*.ngrok.io` | Your domain |
| SSL | Auto (ngrok) | Your certificate |
| Uptime | When running | 24/7 |
| Speed | Slower (tunnel) | Fast (direct) |
| Cost | Free/Paid | Hosting cost |

---

## 💡 Pro Tips

1. **Keep ngrok running** while developing - don't restart unless needed
2. **Use the web interface** (localhost:4040) for debugging
3. **Save your ngrok URL** in a text file for easy reference
4. **Test with test_client.html** first before using real phone calls
5. **Check ngrok logs** if Twilio can't connect
6. **Consider paid plan** if developing frequently (static URL is worth it!)

---

## 🔐 Security Notes

- ngrok tunnels are secure (HTTPS)
- Don't share your ngrok URL publicly (anyone can access it)
- Don't commit ngrok URLs to git
- Auth token is secret - don't share it
- For production, use proper authentication

---

## 📞 Testing Without Phone Calls

You can test the WebSocket connection without Twilio:

### 1. Start server and ngrok
```bash
python main.py
ngrok http 5000
```

### 2. Use test_client.html
Open `test_client.html` in browser and connect to:
```
ws://localhost:5000/media-stream
```

This tests your WebSocket logic without needing Twilio or ngrok!

---

## 🎓 Summary

**ngrok is essential for local development because:**
1. ✅ Exposes localhost to the internet
2. ✅ Provides HTTPS automatically
3. ✅ Allows Twilio to reach your local server
4. ✅ Includes debugging tools
5. ✅ Easy to set up and use

**Remember:**
- ngrok for **development** ✅
- Real hosting for **production** ✅
- Update Twilio webhook when ngrok URL changes ⚠️

Happy developing! 🚀
