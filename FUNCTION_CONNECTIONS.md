# Function Connections & Dependencies Map

## 🔗 Function Relationship Matrix

This document shows how all functions in `main.py` are connected and depend on each other.

---

## 📊 Function Dependency Graph

```
main.py execution
    │
    └─► if __name__ == "__main__":
            │
            └─► uvicorn.run(app)  ──────┐
                                        │
                                        ▼
                            ┌───────────────────────┐
                            │   FastAPI App Ready   │
                            │   Listening on :5000  │
                            └───────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
        ┌─────────────────────┐              ┌──────────────────────┐
        │ POST /incoming-call │              │ WS /media-stream     │
        │                     │              │                      │
        │ handle_incoming_    │              │ handle_media_stream()│
        │ call()              │              │                      │
        └─────────────────────┘              └──────────────────────┘
                    │                                       │
                    │                                       │
                    │ Returns TwiML                         │
                    │ pointing to ──────────────────────────┘
                    │ /media-stream
                    │
                    └─► Twilio connects to WebSocket


handle_media_stream() calls:
    │
    ├─► websocket.accept()
    │
    ├─► asyncio.Queue() × 2
    │
    ├─► sts_connect() ──────────────────┐
    │       │                           │
    │       └─► Returns WebSocket       │
    │           to Deepgram             │
    │                                   │
    ├─► load_config() ──────────────────┤
    │       │                           │
    │       └─► Returns config dict     │
    │                                   │
    └─► asyncio.gather() ───────────────┘
            │
            ├─► twilio_receiver(websocket, audio_queue, streamsid_queue)
            │       │
            │       └─► Produces data for other tasks
            │
            ├─► sts_sender(sts_ws, audio_queue)
            │       │
            │       └─► Consumes from audio_queue
            │
            └─► sts_receiver(sts_ws, websocket, streamsid_queue)
                    │
                    ├─► Consumes from streamsid_queue
                    │
                    └─► Calls handle_text_message()
                            │
                            └─► Calls handle_barge_in()
```

---

## 🎯 Function Call Hierarchy

### Level 0: Entry Point
```
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
```
- **Dependencies:** None
- **Calls:** FastAPI app initialization
- **Purpose:** Start the web server

---

### Level 1: HTTP/WebSocket Endpoints

#### Function: `handle_incoming_call(request)`
```python
@app.post("/incoming-call")
async def handle_incoming_call(request: Request)
```

**Called by:** Twilio (external HTTP POST)

**Calls:** None

**Returns:** TwiML XML response

**Dependencies:**
- `request.url.hostname` - To get server URL
- `request.headers.get("host")` - For ngrok support

**Data Flow:**
```
Twilio → handle_incoming_call() → TwiML Response → Twilio
```

---

#### Function: `handle_media_stream(websocket)`
```python
@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket)
```

**Called by:** Twilio (WebSocket connection)

**Calls:**
1. `websocket.accept()`
2. `sts_connect()`
3. `load_config()`
4. `asyncio.gather()` with:
   - `sts_sender()`
   - `sts_receiver()`
   - `twilio_receiver()`

**Returns:** Nothing (runs until call ends)

**Dependencies:**
- `asyncio.Queue` - For creating queues
- `asyncio.gather` - For concurrent execution
- WebSocket connection from Twilio

**Data Flow:**
```
Twilio WebSocket → handle_media_stream() → Launches 3 tasks
```

---

### Level 2: Configuration & Connection Functions

#### Function: `sts_connect()`
```python
def sts_connect()
```

**Called by:** `handle_media_stream()`

**Calls:**
- `os.getenv("DEEPGRAM_API_KEY")`
- `websockets.connect()`

**Returns:** WebSocket connection context manager

**Dependencies:**
- Environment variable: `DEEPGRAM_API_KEY`
- `websockets` library

**Used by:**
- `handle_media_stream()` (in async with statement)

**Connection Details:**
```
URI: wss://agent.deepgram.com/v1/agent/converse
Auth: API key via subprotocol
```

---

#### Function: `load_config()`
```python
def load_config()
```

**Called by:** `handle_media_stream()`

**Calls:**
- `open("config.json", "r")`
- `json.load()`

**Returns:** Dictionary with agent configuration

**Dependencies:**
- File: `config.json` must exist

**Used by:**
- `handle_media_stream()` (sent to Deepgram)

**Configuration Structure:**
```json
{
  "type": "Settings",
  "audio": {...},
  "agent": {
    "listen": {...},
    "think": {...},
    "speak": {...},
    "greeting": "..."
  }
}
```

---

### Level 3: Concurrent Task Functions

These three functions run simultaneously via `asyncio.gather()`.

#### Function: `twilio_receiver(twilio_ws, audio_queue, streamsid_queue)`
```python
async def twilio_receiver(twilio_ws: WebSocket, audio_queue, streamsid_queue)
```

**Called by:** `asyncio.gather()` in `handle_media_stream()`

**Calls:**
- `twilio_ws.receive_text()` - Repeatedly
- `json.loads()` - Parse messages
- `base64.b64decode()` - Decode audio
- `streamsid_queue.put_nowait()` - Once
- `audio_queue.put_nowait()` - Multiple times

**Returns:** Nothing (runs until "stop" event)

**Dependencies:**
- Twilio WebSocket connection
- Two asyncio queues

**Role:** Producer
- Produces: `streamsid` → `streamsid_queue`
- Produces: Audio chunks → `audio_queue`

**Event Handling:**
| Event | Action |
|-------|--------|
| "start" | Extract streamSid → put in queue |
| "connected" | Ignore |
| "media" | Decode audio → buffer → queue when full |
| "stop" | Exit loop |

**Buffer Management:**
```python
BUFFER_SIZE = 20 * 160  # 3200 bytes = 400ms
inbuffer = bytearray(b"")

# Accumulate until buffer is full
while len(inbuffer) >= BUFFER_SIZE:
    chunk = inbuffer[:BUFFER_SIZE]
    audio_queue.put_nowait(chunk)
    inbuffer = inbuffer[BUFFER_SIZE:]
```

---

#### Function: `sts_sender(sts_ws, audio_queue)`
```python
async def sts_sender(sts_ws, audio_queue)
```

**Called by:** `asyncio.gather()` in `handle_media_stream()`

**Calls:**
- `audio_queue.get()` - Repeatedly (blocks until available)
- `sts_ws.send()` - Send to Deepgram

**Returns:** Nothing (runs forever)

**Dependencies:**
- Deepgram WebSocket connection
- `audio_queue` (populated by `twilio_receiver`)

**Role:** Consumer
- Consumes: Audio chunks from `audio_queue`
- Sends to: Deepgram WebSocket

**Flow:**
```
audio_queue.get() → chunk → sts_ws.send(chunk) → Deepgram
```

**Blocking Behavior:**
- `await audio_queue.get()` blocks if queue is empty
- Resumes when `twilio_receiver` adds a chunk
- This creates natural backpressure

---

#### Function: `sts_receiver(sts_ws, twilio_ws, streamsid_queue)`
```python
async def sts_receiver(sts_ws, twilio_ws: WebSocket, streamsid_queue)
```

**Called by:** `asyncio.gather()` in `handle_media_stream()`

**Calls:**
- `streamsid_queue.get()` - Once at start
- `handle_text_message()` - For JSON messages
- `base64.b64encode()` - For audio messages
- `twilio_ws.send_text()` - Send to Twilio

**Returns:** Nothing (runs until WebSocket closes)

**Dependencies:**
- Deepgram WebSocket connection
- Twilio WebSocket connection
- `streamsid_queue` (populated by `twilio_receiver`)

**Role:** Consumer & Sender
- Consumes: `streamsid` from `streamsid_queue`
- Receives: Messages from Deepgram
- Sends: Audio to Twilio

**Message Type Handling:**
```python
async for message in sts_ws:
    if type(message) is str:
        # JSON message (events, transcriptions)
        decoded = json.loads(message)
        await handle_text_message(decoded, twilio_ws, sts_ws, streamsid)
    else:
        # Binary message (audio)
        raw_mulaw = message
        # Encode and send to Twilio
```

---

### Level 4: Event Handler Functions

#### Function: `handle_text_message(decoded, twilio_ws, sts_ws, streamsid)`
```python
async def handle_text_message(decoded, twilio_ws: WebSocket, sts_ws, streamsid)
```

**Called by:** `sts_receiver()`

**Calls:**
- `handle_barge_in()`

**Returns:** Nothing

**Dependencies:**
- Parsed JSON message from Deepgram
- Twilio WebSocket connection
- Deepgram WebSocket connection
- Stream ID

**Purpose:** Route text messages to appropriate handlers

**Current Implementation:**
- Only handles barge-in events
- Can be extended for other message types

---

#### Function: `handle_barge_in(decoded, twilio_ws, streamsid)`
```python
async def handle_barge_in(decoded, twilio_ws: WebSocket, streamsid)
```

**Called by:** `handle_text_message()`

**Calls:**
- `twilio_ws.send_text()` - If barge-in detected

**Returns:** Nothing

**Dependencies:**
- Parsed JSON message
- Twilio WebSocket connection
- Stream ID

**Logic:**
```python
if decoded["type"] == "UserStartedSpeaking":
    clear_message = {
        "event": "clear",
        "streamSid": streamsid
    }
    await twilio_ws.send_text(json.dumps(clear_message))
```

**Effect:**
- Stops AI's current audio playback
- Allows user's new input to be processed

---

## 🔄 Data Flow Between Functions

### Queue-Based Communication

#### audio_queue
```
Producer: twilio_receiver()
    │
    ├─ Receives audio from Twilio
    ├─ Decodes base64
    ├─ Buffers to 3200 bytes
    └─ Puts in queue
        │
        ▼
    audio_queue
        │
        ▼
Consumer: sts_sender()
    │
    ├─ Gets from queue (blocks if empty)
    └─ Sends to Deepgram
```

#### streamsid_queue
```
Producer: twilio_receiver()
    │
    ├─ Receives "start" event
    ├─ Extracts streamSid
    └─ Puts in queue (once)
        │
        ▼
    streamsid_queue
        │
        ▼
Consumer: sts_receiver()
    │
    ├─ Gets from queue (blocks until available)
    └─ Uses for all subsequent messages
```

---

## 🎭 Function Roles & Responsibilities

### Configuration Functions
| Function | Role | When Called | Returns |
|----------|------|-------------|---------|
| `sts_connect()` | Create Deepgram connection | Once per call | WebSocket context |
| `load_config()` | Load agent settings | Once per call | Config dict |

### Endpoint Functions
| Function | Role | When Called | Returns |
|----------|------|-------------|---------|
| `handle_incoming_call()` | Return TwiML | Per call start | XML response |
| `handle_media_stream()` | Orchestrate call | Per call | None (runs until end) |

### Task Functions (Concurrent)
| Function | Role | Runs | Communicates Via |
|----------|------|------|------------------|
| `twilio_receiver()` | Get audio from Twilio | Until "stop" | Queues (producer) |
| `sts_sender()` | Send audio to Deepgram | Forever | Queue (consumer) |
| `sts_receiver()` | Get AI response | Until WS closes | Queue (consumer) |

### Event Handler Functions
| Function | Role | When Called | Effect |
|----------|------|-------------|--------|
| `handle_text_message()` | Route text events | Per JSON message | Calls handlers |
| `handle_barge_in()` | Handle interruptions | On user speech | Clears Twilio audio |

---

## 🔀 Execution Timeline

Here's what happens in chronological order:

### T=0: Server Starts
```
1. Python executes main.py
2. FastAPI app initializes
3. uvicorn.run() starts server
4. Server listens on 0.0.0.0:5000
```

### T=1: Call Received
```
5. Twilio receives call
6. Twilio POSTs to /incoming-call
7. handle_incoming_call() executes
8. Returns TwiML with WebSocket URL
9. Twilio receives TwiML
```

### T=2: WebSocket Connection
```
10. Twilio connects to /media-stream
11. handle_media_stream() executes
12. websocket.accept() completes
13. Creates audio_queue
14. Creates streamsid_queue
```

### T=3: Deepgram Setup
```
15. sts_connect() creates WebSocket
16. load_config() reads config.json
17. Sends config to Deepgram
18. Deepgram acknowledges
```

### T=4: Tasks Launch
```
19. asyncio.gather() starts three tasks:
    ├─ twilio_receiver() starts
    ├─ sts_sender() starts (blocks on empty queue)
    └─ sts_receiver() starts (blocks on empty queue)
```

### T=5: First Messages
```
20. Twilio sends "start" event
21. twilio_receiver() extracts streamSid
22. Puts streamSid in streamsid_queue
23. sts_receiver() unblocks, gets streamSid
```

### T=6: Greeting Plays
```
24. Deepgram sends greeting audio
25. sts_receiver() receives it
26. Encodes as base64
27. Sends to Twilio
28. User hears greeting
```

### T=7: User Speaks
```
29. Twilio sends "media" events
30. twilio_receiver() decodes audio
31. Buffers until 3200 bytes
32. Puts chunk in audio_queue
33. sts_sender() unblocks, gets chunk
34. Sends to Deepgram
```

### T=8: AI Processes
```
35. Deepgram transcribes (STT)
36. Sends to GPT-4o-mini
37. GPT generates response
38. Deepgram synthesizes (TTS)
39. Sends audio back
```

### T=9: User Hears Response
```
40. sts_receiver() gets audio
41. Encodes as base64
42. Sends to Twilio
43. Twilio plays to user
```

### T=10: Barge-in (Optional)
```
44. User interrupts AI
45. Deepgram detects speech
46. Sends {"type": "UserStartedSpeaking"}
47. sts_receiver() receives it
48. Calls handle_text_message()
49. Calls handle_barge_in()
50. Sends "clear" to Twilio
51. Twilio stops playback
```

### T=11: Call Ends
```
52. User hangs up
53. Twilio sends "stop" event
54. twilio_receiver() breaks loop
55. Other tasks complete/cancel
56. WebSockets close
57. Resources cleaned up
```

---

## 🧩 Function Interdependencies

### Critical Dependencies

**handle_media_stream() depends on:**
- `sts_connect()` - Must succeed to continue
- `load_config()` - Must succeed to configure Deepgram
- All three tasks must run concurrently

**twilio_receiver() depends on:**
- Twilio sending "start" event first
- Valid base64-encoded audio in "media" events

**sts_sender() depends on:**
- `twilio_receiver()` populating audio_queue
- Deepgram WebSocket being open

**sts_receiver() depends on:**
- `twilio_receiver()` providing streamSid
- Deepgram sending responses

**handle_barge_in() depends on:**
- `sts_receiver()` passing correct message format
- Valid streamSid from earlier

---

## 🎯 Function Coupling Analysis

### Tight Coupling
These functions are tightly coupled (must work together):

```
handle_media_stream() ←→ sts_connect()
handle_media_stream() ←→ load_config()
twilio_receiver() ←→ sts_sender() (via audio_queue)
twilio_receiver() ←→ sts_receiver() (via streamsid_queue)
handle_text_message() ←→ handle_barge_in()
```

### Loose Coupling
These functions are loosely coupled (independent):

```
handle_incoming_call() ← → handle_media_stream()
  (Only connected via Twilio's TwiML interpretation)

sts_sender() ← → sts_receiver()
  (Both use Deepgram WS but don't directly communicate)
```

---

## 🔧 Modification Impact Analysis

### If you modify `twilio_receiver()`:
**Impacts:**
- `sts_sender()` - If you change audio_queue format
- `sts_receiver()` - If you change streamsid_queue format
- Buffer size affects latency

### If you modify `sts_receiver()`:
**Impacts:**
- `handle_text_message()` - If you change message format
- Twilio playback - If you change audio encoding

### If you modify `handle_barge_in()`:
**Impacts:**
- User experience - Changes interruption behavior
- Minimal impact on other functions

### If you modify `config.json`:
**Impacts:**
- AI personality
- Voice model
- Audio quality
- No code changes needed

---

## 📝 Summary

### Function Count: 10

**Entry Point:** 1
- `if __name__ == "__main__"`

**Endpoints:** 2
- `handle_incoming_call()`
- `handle_media_stream()`

**Configuration:** 2
- `sts_connect()`
- `load_config()`

**Concurrent Tasks:** 3
- `twilio_receiver()`
- `sts_sender()`
- `sts_receiver()`

**Event Handlers:** 2
- `handle_text_message()`
- `handle_barge_in()`

### Key Connections:
1. **Queues** connect `twilio_receiver` with `sts_sender` and `sts_receiver`
2. **WebSockets** connect to Twilio and Deepgram
3. **Event handlers** process special messages
4. **Config** defines AI behavior

### Critical Path:
```
User speaks → Twilio → twilio_receiver → audio_queue → 
sts_sender → Deepgram → AI processing → sts_receiver → 
Twilio → User hears
```

This architecture enables **real-time, bidirectional voice communication** with **natural interruption handling**!
