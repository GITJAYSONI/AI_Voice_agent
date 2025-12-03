# Quick Reference Guide - Main.py

## 🎯 One-Page Overview

### What This Project Does
An AI voice agent that acts as a virtual doctor, capable of having real-time phone conversations using:
- **Twilio** for phone calls
- **Deepgram** for speech recognition and synthesis
- **OpenAI GPT-4o-mini** for intelligent responses

---

## 📁 File Structure

```
Ai-voice-agent/
├── main.py                          # Main application (THIS FILE)
├── config.json                      # AI agent configuration
├── .env                             # API keys (DEEPGRAM_API_KEY)
├── test_client.html                 # Browser-based test client
├── README.md                        # Project documentation
└── MAIN_PY_DETAILED_EXPLANATION.md  # Detailed explanation (NEW)
└── WORKFLOW_DIAGRAM.md              # Visual workflow (NEW)
└── FUNCTION_CONNECTIONS.md          # Function dependencies (NEW)
```

---

## 🔑 Key Concepts

### 1. **Async/Await**
Everything runs asynchronously to handle multiple operations simultaneously without blocking.

### 2. **WebSockets**
Real-time bidirectional communication:
- Twilio ←→ Your Server
- Your Server ←→ Deepgram

### 3. **Queues**
Thread-safe data passing between concurrent tasks:
- `audio_queue` - Audio from Twilio to Deepgram
- `streamsid_queue` - Stream ID from Twilio to receiver

### 4. **Concurrent Tasks**
Three tasks run simultaneously:
- **twilio_receiver** - Gets audio from phone
- **sts_sender** - Sends audio to Deepgram
- **sts_receiver** - Gets AI response and plays it back

---

## 📊 10 Functions at a Glance

| # | Function | Purpose | Lines |
|---|----------|---------|-------|
| 1 | `sts_connect()` | Connect to Deepgram | 14-23 |
| 2 | `load_config()` | Load config.json | 25-27 |
| 3 | `handle_barge_in()` | Stop AI when user interrupts | 29-35 |
| 4 | `handle_text_message()` | Process JSON messages | 37-38 |
| 5 | `sts_sender()` | Send audio to Deepgram | 40-44 |
| 6 | `sts_receiver()` | Receive AI responses | 46-63 |
| 7 | `twilio_receiver()` | Receive audio from Twilio | 65-97 |
| 8 | `handle_incoming_call()` | Return TwiML for call setup | 99-115 |
| 9 | `handle_media_stream()` | Main orchestrator | 117-134 |
| 10 | `if __name__ == "__main__"` | Start server | 136-138 |

---

## 🔄 Simple Flow Diagram

```
📱 User Calls
    ↓
☁️ Twilio
    ↓
🌐 /incoming-call → Returns TwiML
    ↓
🔌 /media-stream (WebSocket)
    ↓
┌───────────────────────────────┐
│   3 Concurrent Tasks Start    │
├───────────────────────────────┤
│ 1. twilio_receiver            │ ← Receives audio from phone
│ 2. sts_sender                 │ ← Sends audio to Deepgram
│ 3. sts_receiver               │ ← Gets AI response
└───────────────────────────────┘
    ↓
🤖 Deepgram (STT → GPT → TTS)
    ↓
🔊 User Hears AI Response
```

---

## 💬 Message Flow

### Incoming (User → AI)
```
User speaks
  → Twilio (mulaw audio)
  → base64 encode
  → Your server
  → Decode & buffer (3200 bytes)
  → Send to Deepgram
  → STT (Nova-3)
  → GPT-4o-mini
  → TTS (Aura-2)
```

### Outgoing (AI → User)
```
Deepgram TTS
  → Your server
  → base64 encode
  → Twilio
  → User hears
```

---

## 🎛️ Configuration (config.json)

```json
{
  "audio": {
    "input/output": "mulaw @ 8000 Hz"
  },
  "agent": {
    "listen": "Deepgram Nova-3",      // Speech-to-Text
    "think": "GPT-4o-mini",            // AI Brain
    "speak": "Deepgram Aura-2",        // Text-to-Speech
    "greeting": "Hello, this is..."    // First message
  }
}
```

---

## 🔧 How to Run

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn websockets python-dotenv
   ```

2. **Set environment variable:**
   ```
   # .env file
   DEEPGRAM_API_KEY=your_key_here
   ```

3. **Run server:**
   ```bash
   python main.py
   ```

4. **Expose to internet (for Twilio):**
   ```bash
   ngrok http 5000
   ```

5. **Configure Twilio:**
   - Set webhook URL to: `https://your-ngrok-url.ngrok.io/incoming-call`

---

## 🐛 Common Issues & Solutions

### Issue: "DEEPGRAM_API_KEY is not found"
**Solution:** Create `.env` file with your API key

### Issue: Twilio can't connect
**Solution:** 
- Check ngrok is running
- Verify webhook URL in Twilio console
- Ensure server is on port 5000

### Issue: No audio or choppy audio
**Solution:**
- Check internet connection
- Verify mulaw encoding in config
- Check buffer size (3200 bytes = 400ms)

### Issue: AI doesn't respond
**Solution:**
- Check Deepgram API key is valid
- Verify config.json is properly formatted
- Check console for error messages

---

## 📈 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Buffer Size | 3200 bytes | 400ms of audio |
| Sample Rate | 8000 Hz | Phone quality |
| Encoding | mulaw | Telephony standard |
| Latency | 1.3-2.1s | Total response time |
| Concurrent Tasks | 3 | Run simultaneously |

---

## 🎨 Customization Points

### Change AI Personality
Edit `config.json` → `agent.think.prompt`

### Change Voice
Edit `config.json` → `agent.speak.provider.model`
- Options: aura-2-thalia-en, aura-2-zeus-en, etc.

### Change Greeting
Edit `config.json` → `agent.greeting`

### Adjust Buffer Size
Edit `main.py` line 66:
```python
BUFFER_SIZE = 20 * 160  # Increase/decrease for latency trade-off
```

### Change AI Model
Edit `config.json` → `agent.think.provider.model`
- Options: gpt-4o-mini, gpt-4o, gpt-3.5-turbo

---

## 🔐 Security Checklist

- ✅ API keys in `.env` (not in code)
- ✅ `.env` in `.gitignore`
- ✅ HTTPS for production (ngrok provides this)
- ✅ Validate incoming requests from Twilio
- ⚠️ Consider rate limiting for production
- ⚠️ Add authentication for sensitive deployments

---

## 📚 Related Documentation

1. **MAIN_PY_DETAILED_EXPLANATION.md** - Deep dive into each function
2. **WORKFLOW_DIAGRAM.md** - Visual architecture diagrams
3. **FUNCTION_CONNECTIONS.md** - Function dependencies and call hierarchy
4. **README.md** - Project overview and setup

---

## 🎯 Key Takeaways

1. **Three concurrent tasks** handle bidirectional audio streaming
2. **Queues** enable communication between tasks
3. **WebSockets** provide real-time connections
4. **Barge-in** allows natural interruptions
5. **Config-driven** - Change AI behavior without code changes

---

## 🚀 Next Steps

### To Understand Better:
1. Read `MAIN_PY_DETAILED_EXPLANATION.md` for function details
2. Review `WORKFLOW_DIAGRAM.md` for visual flow
3. Check `FUNCTION_CONNECTIONS.md` for dependencies

### To Extend:
1. Add conversation history tracking
2. Implement call recording
3. Add multiple language support
4. Create admin dashboard
5. Add analytics and logging

### To Deploy:
1. Use a cloud service (AWS, GCP, Azure)
2. Set up proper domain with SSL
3. Configure production environment variables
4. Set up monitoring and alerts
5. Implement proper error handling

---

## 🆘 Quick Debug Commands

```bash
# Check if server is running
curl http://localhost:5000/docs

# View server logs
# (Just watch the console where you ran python main.py)

# Test WebSocket connection
# Use test_client.html in browser

# Check environment variables
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DEEPGRAM_API_KEY'))"
```

---

## 📞 Call Flow Cheat Sheet

```
1. User dials → Twilio receives
2. Twilio POSTs to /incoming-call
3. Server returns TwiML with WebSocket URL
4. Twilio connects to /media-stream
5. Server launches 3 tasks
6. Deepgram plays greeting
7. User speaks → transcribed → GPT → TTS → user hears
8. Repeat step 7 until call ends
9. User hangs up → cleanup
```

---

## 🎓 Learning Path

**Beginner:**
- Understand the call flow
- Know what each function does
- Run the project successfully

**Intermediate:**
- Understand async/await patterns
- Modify configuration
- Customize AI personality

**Advanced:**
- Add new features
- Optimize performance
- Deploy to production
- Handle edge cases

---

## 💡 Pro Tips

1. **Use test_client.html** for testing without phone calls
2. **Monitor console output** for debugging
3. **Start with small buffer sizes** for lower latency (but more CPU)
4. **Use GPT-4o-mini** for cost-effective development
5. **Test barge-in** by interrupting the AI mid-sentence
6. **Check Deepgram docs** for more voice options
7. **Use ngrok's web interface** (http://localhost:4040) to inspect requests

---

## 🎬 That's It!

You now have a complete understanding of how this AI voice agent works. The system is elegant in its simplicity:

- **2 endpoints** (HTTP + WebSocket)
- **3 concurrent tasks** (receive, send, respond)
- **2 queues** (audio + stream ID)
- **1 goal** (natural voice conversations)

Happy coding! 🚀
