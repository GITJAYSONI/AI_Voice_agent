# Main.py - Detailed Explanation & Workflow

## 📋 Project Overview

This is an **AI Voice Agent** that acts as a virtual doctor (Dr. Jay Soni) capable of having real-time voice conversations over phone calls. The system integrates:

- **Twilio** - For phone call handling
- **Deepgram** - For Speech-to-Text (STT) and Text-to-Speech (TTS)
- **OpenAI GPT-4o-mini** - For intelligent conversation
- **FastAPI** - Web framework for handling HTTP and WebSocket connections

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHONE CALL FLOW                              │
└─────────────────────────────────────────────────────────────────┘

User makes call → Twilio receives → Sends to your server
                                            ↓
                                    /incoming-call endpoint
                                            ↓
                                    Returns TwiML response
                                            ↓
                            Twilio connects to /media-stream WebSocket
                                            ↓
                        ┌───────────────────────────────────┐
                        │   Three Concurrent Tasks Start    │
                        └───────────────────────────────────┘
                                    ↓
        ┌───────────────────────────┼───────────────────────────┐
        ↓                           ↓                           ↓
  twilio_receiver          sts_sender                  sts_receiver
  (Gets audio from         (Sends audio to            (Gets AI response
   phone call)              Deepgram)                  from Deepgram)
        ↓                           ↓                           ↓
   audio_queue ──────────────→ Deepgram STT ────────→ GPT-4o-mini
                                                              ↓
                                                        Deepgram TTS
                                                              ↓
                                                    Back to Twilio → User hears
```

---

## 📦 Dependencies & Imports (Lines 1-8)

```python
import asyncio          # For async/concurrent operations
import base64           # For encoding/decoding audio data
import json             # For parsing JSON messages
import os               # For environment variables
import websockets       # For WebSocket client (to Deepgram)
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv  # For loading .env file
```

**Why these imports?**
- `asyncio` - The entire system runs asynchronously to handle multiple tasks simultaneously
- `base64` - Twilio sends audio as base64-encoded strings
- `websockets` - To connect to Deepgram's WebSocket API
- `FastAPI` - Modern web framework with built-in WebSocket support

---

## 🔧 Configuration Functions

### 1. `sts_connect()` (Lines 14-23)

```python
def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY is not found")
    
    return websockets.connect(
        uri="wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )
```

**Purpose:** Creates a WebSocket connection to Deepgram's Agent API

**What it does:**
1. Retrieves the Deepgram API key from environment variables
2. Validates the key exists
3. Returns a WebSocket connection object to Deepgram's conversational AI endpoint
4. Uses the API key as a subprotocol for authentication

**When it's called:** When a new call comes in (in `handle_media_stream`)

---

### 2. `load_config()` (Lines 25-27)

```python
def load_config():
    with open("config.json", "r") as f:
        return json.load(f)
```

**Purpose:** Loads the AI agent configuration

**What it does:**
1. Opens `config.json` file
2. Parses it as JSON
3. Returns the configuration dictionary

**Configuration includes:**
- Audio settings (mulaw encoding, 8000 Hz sample rate)
- Speech-to-Text provider (Deepgram Nova-3)
- AI thinking provider (GPT-4o-mini)
- Text-to-Speech provider (Deepgram Aura-2)
- Agent personality and greeting

**When it's called:** When establishing the Deepgram connection

---

## 🎯 Core Handler Functions

### 3. `handle_barge_in()` (Lines 29-35)

```python
async def handle_barge_in(decoded, twilio_ws: WebSocket, streamsid):
    if decoded["type"] == "UserStartedSpeaking":
        clear_message = {
            "event": "clear",
            "streamSid": streamsid
        }
        await twilio_ws.send_text(json.dumps(clear_message))
```

**Purpose:** Implements "barge-in" functionality - allows users to interrupt the AI

**What is Barge-in?**
When a user starts speaking while the AI is still talking, this function:
1. Detects the interruption (via `UserStartedSpeaking` event from Deepgram)
2. Sends a "clear" command to Twilio
3. Stops the AI's current audio playback
4. Allows the new user input to be processed immediately

**Why it's important:**
Makes conversations feel natural - just like talking to a real person who stops talking when you interrupt them.

**Parameters:**
- `decoded` - The parsed JSON message from Deepgram
- `twilio_ws` - WebSocket connection to Twilio
- `streamsid` - Unique identifier for this audio stream

---

### 4. `handle_text_message()` (Lines 37-38)

```python
async def handle_text_message(decoded, twilio_ws: WebSocket, sts_ws, streamsid):
    await handle_barge_in(decoded, twilio_ws, streamsid)
```

**Purpose:** Processes text-based messages from Deepgram

**What it does:**
Currently, it only handles barge-in events, but this function serves as a router for all text/JSON messages from Deepgram (as opposed to binary audio data).

**Potential future uses:**
- Processing transcription results
- Handling conversation state changes
- Managing agent events

---

## 🔄 The Three Concurrent Tasks

These three functions run simultaneously using `asyncio.gather()` to create a bidirectional audio pipeline.

### 5. `sts_sender()` (Lines 40-44)

```python
async def sts_sender(sts_ws, audio_queue):
    print("sts_sender started")
    while True:
        chunk = await audio_queue.get()
        await sts_ws.send(chunk)
```

**Purpose:** Continuously sends audio from the phone call to Deepgram

**Flow:**
1. Waits for audio chunks to appear in `audio_queue`
2. Gets a chunk (this blocks until one is available)
3. Sends it to Deepgram via WebSocket
4. Repeats forever

**Data Flow:**
```
User speaks → Twilio → twilio_receiver → audio_queue → sts_sender → Deepgram
```

**Audio Format:** Raw mulaw-encoded audio at 8000 Hz (phone quality)

---

### 6. `sts_receiver()` (Lines 46-63)

```python
async def sts_receiver(sts_ws, twilio_ws: WebSocket, streamsid_queue):
    print("sts_receiver started")
    streamsid = await streamsid_queue.get()

    async for message in sts_ws:
        if type(message) is str:
            decoded = json.loads(message)
            await handle_text_message(decoded, twilio_ws, sts_ws, streamsid)
            continue
        
        raw_mulaw = message

        media_message = {
            "event": "media",
            "streamSid": streamsid,
            "media": {"payload": base64.b64encode(raw_mulaw).decode("ascii")}
        }
        await twilio_ws.send_text(json.dumps(media_message))
```

**Purpose:** Receives AI responses from Deepgram and sends them to Twilio

**Flow:**
1. Waits for the `streamsid` (stream identifier) from Twilio
2. Listens for messages from Deepgram
3. If message is text (JSON):
   - Parses it
   - Handles events like barge-in
4. If message is binary (audio):
   - Encodes it as base64
   - Wraps it in Twilio's media message format
   - Sends to Twilio for playback

**Data Flow:**
```
Deepgram → sts_receiver → Twilio → User hears AI response
```

**Message Types:**
- **String messages:** Events, transcriptions, metadata
- **Binary messages:** AI-generated speech audio

---

### 7. `twilio_receiver()` (Lines 65-97)

```python
async def twilio_receiver(twilio_ws: WebSocket, audio_queue, streamsid_queue):
    BUFFER_SIZE = 20 * 160
    inbuffer = bytearray(b"")

    try:
        while True:
            message = await twilio_ws.receive_text()
            data = json.loads(message)
            event = data["event"]

            if event == "start":
                print("get our streamsid")
                start = data["start"]
                streamsid = start["streamSid"]
                streamsid_queue.put_nowait(streamsid)
            elif event == "connected":
                continue
            elif event == "media":
                media = data["media"]
                chunk = base64.b64decode(media["payload"])
                if media["track"] == "inbound":
                    inbuffer.extend(chunk)
            elif event == "stop":
                break

            while len(inbuffer) >= BUFFER_SIZE:
                chunk = inbuffer[:BUFFER_SIZE]
                audio_queue.put_nowait(chunk)
                inbuffer = inbuffer[BUFFER_SIZE:]
    except WebSocketDisconnect:
        print("Twilio disconnected")
    except Exception as e:
        print(f"Error in twilio_receiver: {e}")
```

**Purpose:** Receives audio from Twilio and buffers it for processing

**Key Concepts:**

**1. Buffer Size (Line 66):**
```python
BUFFER_SIZE = 20 * 160  # = 3200 bytes
```
- 160 bytes = 20ms of mulaw audio at 8000 Hz
- 20 * 160 = 400ms chunks (0.4 seconds)
- Larger chunks reduce processing overhead

**2. Event Handling:**

| Event | Action |
|-------|--------|
| `start` | Extract and store the stream ID |
| `connected` | Ignore (just a connection confirmation) |
| `media` | Decode and buffer audio data |
| `stop` | End the call |

**3. Buffering Logic (Lines 90-93):**
```python
while len(inbuffer) >= BUFFER_SIZE:
    chunk = inbuffer[:BUFFER_SIZE]
    audio_queue.put_nowait(chunk)
    inbuffer = inbuffer[BUFFER_SIZE:]
```

**Why buffering?**
- Twilio sends small audio chunks frequently
- We accumulate them until we have enough for efficient processing
- Then we send complete chunks to Deepgram

**Data Flow:**
```
Twilio → base64 decode → inbuffer → chunk (when full) → audio_queue
```

---

## 🌐 HTTP & WebSocket Endpoints

### 8. `/incoming-call` Endpoint (Lines 99-115)

```python
@app.post("/incoming-call")
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML to connect to the media stream."""
    host = request.url.hostname
    host = request.headers.get("host", host)
    
    response = f"""<Response>
    <Connect>
        <Stream url="wss://{host}/media-stream" />
    </Connect>
</Response>"""
    return HTMLResponse(content=response, media_type="application/xml")
```

**Purpose:** First point of contact when a call comes in

**Flow:**
1. Twilio makes a POST request to this endpoint when someone calls your number
2. The function extracts the host (your server's URL)
3. Returns TwiML (Twilio Markup Language) XML
4. TwiML tells Twilio to connect the call's audio to your `/media-stream` WebSocket

**TwiML Breakdown:**
```xml
<Response>              <!-- Root element -->
  <Connect>             <!-- Connect to a stream -->
    <Stream url="wss://{host}/media-stream" />  <!-- WebSocket URL -->
  </Connect>
</Response>
```

**Why the host logic?**
When using ngrok (for local development), we need the public ngrok URL, not "localhost"

---

### 9. `/media-stream` WebSocket (Lines 117-134)

```python
@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle the WebSocket connection for the media stream."""
    await websocket.accept()
    print("Twilio connected to media stream")

    audio_queue = asyncio.Queue()
    streamsid_queue = asyncio.Queue()

    async with sts_connect() as sts_ws:
        config_message = load_config()
        await sts_ws.send(json.dumps(config_message))

        await asyncio.gather(
            sts_sender(sts_ws, audio_queue),
            sts_receiver(sts_ws, websocket, streamsid_queue),
            twilio_receiver(websocket, audio_queue, streamsid_queue)
        )
```

**Purpose:** Main orchestrator - manages the entire call lifecycle

**Step-by-step breakdown:**

**1. Accept Connection (Line 120):**
```python
await websocket.accept()
```
Establishes the WebSocket connection with Twilio

**2. Create Queues (Lines 123-124):**
```python
audio_queue = asyncio.Queue()        # For audio chunks
streamsid_queue = asyncio.Queue()    # For stream ID
```
These queues enable communication between concurrent tasks

**3. Connect to Deepgram (Line 126):**
```python
async with sts_connect() as sts_ws:
```
Opens WebSocket connection to Deepgram (auto-closes when done)

**4. Send Configuration (Lines 127-128):**
```python
config_message = load_config()
await sts_ws.send(json.dumps(config_message))
```
Tells Deepgram:
- What audio format to expect
- Which AI models to use
- The agent's personality and greeting

**5. Launch Concurrent Tasks (Lines 130-134):**
```python
await asyncio.gather(
    sts_sender(sts_ws, audio_queue),
    sts_receiver(sts_ws, websocket, streamsid_queue),
    twilio_receiver(websocket, audio_queue, streamsid_queue)
)
```

`asyncio.gather()` runs all three functions simultaneously:
- They all run in parallel
- If any one fails, all are cancelled
- The function waits until all complete (or one fails)

---

## 🚀 Application Entry Point

### 10. Main Block (Lines 136-138)

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
```

**Purpose:** Starts the FastAPI server

**Configuration:**
- `host="0.0.0.0"` - Listen on all network interfaces (allows external connections)
- `port=5000` - Server runs on port 5000

**When you run:** `python main.py`
This starts the web server and makes it ready to receive calls

---

## 🔄 Complete Call Flow - Step by Step

Let me walk you through what happens during an actual call:

### Phase 1: Call Initiation
```
1. User dials your Twilio number
2. Twilio receives the call
3. Twilio makes POST request to your /incoming-call endpoint
4. Your server returns TwiML with WebSocket URL
5. Twilio connects to /media-stream WebSocket
```

### Phase 2: Connection Setup
```
6. handle_media_stream() accepts the WebSocket
7. Creates audio_queue and streamsid_queue
8. Connects to Deepgram via sts_connect()
9. Sends config.json to Deepgram
10. Launches three concurrent tasks
```

### Phase 3: Active Conversation
```
┌─────────────────────────────────────────────────────────┐
│                  CONCURRENT TASKS                       │
└─────────────────────────────────────────────────────────┘

Task 1: twilio_receiver
├─ Receives "start" event → extracts streamSid
├─ Puts streamSid in streamsid_queue
├─ Receives "media" events with audio
├─ Decodes base64 audio
├─ Buffers until BUFFER_SIZE reached
└─ Puts chunks in audio_queue

Task 2: sts_sender
├─ Gets chunks from audio_queue
└─ Sends to Deepgram

Task 3: sts_receiver
├─ Gets streamSid from streamsid_queue
├─ Receives from Deepgram:
│  ├─ Text messages (events, transcriptions)
│  └─ Binary messages (AI speech audio)
├─ Handles barge-in events
└─ Sends audio back to Twilio

Deepgram Processing (internal):
├─ Speech-to-Text (Nova-3 model)
├─ GPT-4o-mini processes conversation
└─ Text-to-Speech (Aura-2 model)
```

### Phase 4: User Interruption (Barge-in)
```
1. User starts speaking while AI is talking
2. Deepgram detects this
3. Sends {"type": "UserStartedSpeaking"} to sts_receiver
4. sts_receiver calls handle_text_message
5. handle_barge_in sends "clear" event to Twilio
6. Twilio stops playing current audio
7. New user speech is processed immediately
```

### Phase 5: Call Termination
```
1. User hangs up
2. Twilio sends "stop" event
3. twilio_receiver breaks its loop
4. Other tasks complete or are cancelled
5. Connections close
6. Resources are cleaned up
```

---

## 📊 Data Structures & Queues

### Audio Queue
```python
audio_queue = asyncio.Queue()
```
**Purpose:** Thread-safe queue for passing audio from Twilio to Deepgram

**Flow:**
```
twilio_receiver (producer) → audio_queue → sts_sender (consumer)
```

**Contents:** Raw mulaw audio chunks (3200 bytes each)

### StreamSid Queue
```python
streamsid_queue = asyncio.Queue()
```
**Purpose:** Pass the stream identifier from twilio_receiver to sts_receiver

**Flow:**
```
twilio_receiver (gets from Twilio) → streamsid_queue → sts_receiver (uses for responses)
```

**Contents:** Single string value (the stream ID)

---

## 🎨 Configuration Deep Dive (config.json)

### Audio Settings
```json
"audio": {
    "input": {
        "encoding": "mulaw",
        "sample_rate": 8000
    },
    "output": {
        "encoding": "mulaw",
        "sample_rate": 8000,
        "container": "none"
    }
}
```

**Mulaw Encoding:**
- Logarithmic audio compression
- Standard for telephony
- 8-bit samples at 8000 Hz
- Good quality for voice, small file size

### Agent Configuration

**Listen (STT):**
```json
"listen": {
    "provider": {
        "type": "deepgram",
        "model": "nova-3",
        "keyterms": ["hello", "goodbye"]
    }
}
```
- Uses Deepgram's Nova-3 model for transcription
- Keyterms help with recognition accuracy

**Think (AI):**
```json
"think": {
    "provider": {
        "type": "open_ai",
        "model": "gpt-4o-mini",
        "temperature": 0.7
    },
    "prompt": "You are a professional doctor..."
}
```
- GPT-4o-mini for fast, cost-effective responses
- Temperature 0.7 for balanced creativity
- Prompt defines the AI's personality

**Speak (TTS):**
```json
"speak": {
    "provider": {
        "type": "deepgram",
        "model": "aura-2-thalia-en"
    }
}
```
- Aura-2 for natural-sounding voice
- Thalia voice (female, English)

---

## 🔐 Security & Environment Variables

The `.env` file contains:
```
DEEPGRAM_API_KEY=your_key_here
```

**Why environment variables?**
- Keeps secrets out of code
- Easy to change without modifying code
- Different keys for dev/production

---

## 🐛 Error Handling

The code includes basic error handling:

```python
try:
    # Main loop
except WebSocketDisconnect:
    print("Twilio disconnected")
except Exception as e:
    print(f"Error in twilio_receiver: {e}")
```

**What's handled:**
- WebSocket disconnections (normal hangups)
- General exceptions (logged for debugging)

---

## 💡 Key Design Patterns

### 1. **Async/Await Pattern**
All I/O operations are async to prevent blocking:
```python
await websocket.accept()
await sts_ws.send(data)
chunk = await audio_queue.get()
```

### 2. **Producer-Consumer Pattern**
```
twilio_receiver (producer) → Queue → sts_sender (consumer)
```

### 3. **Context Manager Pattern**
```python
async with sts_connect() as sts_ws:
    # Use connection
# Auto-closes when done
```

### 4. **Event-Driven Architecture**
Different events trigger different handlers:
- "start" → extract stream ID
- "media" → process audio
- "UserStartedSpeaking" → handle barge-in

---

## 📈 Performance Considerations

### 1. **Buffer Size**
```python
BUFFER_SIZE = 20 * 160  # 400ms of audio
```
- Larger = less overhead, more latency
- Smaller = more overhead, less latency
- 400ms is a good balance

### 2. **Concurrent Tasks**
Three tasks run simultaneously for maximum throughput:
- No waiting for one to finish before starting another
- Queues handle synchronization

### 3. **Async I/O**
Non-blocking operations allow handling multiple calls efficiently

---

## 🎯 Summary

**Main.py is the orchestrator that:**

1. **Receives phone calls** via Twilio
2. **Streams audio** to Deepgram for transcription
3. **Processes conversations** using GPT-4o-mini
4. **Generates speech** using Deepgram TTS
5. **Plays responses** back to the caller
6. **Handles interruptions** naturally with barge-in

**The magic happens through:**
- Three concurrent async tasks working together
- Queues for inter-task communication
- WebSocket connections for real-time bidirectional audio
- Event-driven architecture for responsive interactions

**The result:**
A natural-feeling AI doctor that can have real-time voice conversations over the phone!
