import asyncio
import base64
import json
import os
import websockets
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

def sts_connect():
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise Exception("DEEPGRAM_API_KEY is not found")
    
    # Keep using websockets library for the client-side connection to Deepgram
    return websockets.connect(
        uri="wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", api_key]
    )

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

async def handle_barge_in(decoded, twilio_ws: WebSocket, streamsid):
    if decoded["type"] == "UserStartedSpeaking":
        clear_message = {
            "event": "clear",
            "streamSid": streamsid
        }
        await twilio_ws.send_text(json.dumps(clear_message))

async def handle_text_message(decoded, twilio_ws: WebSocket, sts_ws, streamsid):
    await handle_barge_in(decoded, twilio_ws, streamsid)

async def sts_sender(sts_ws, audio_queue):
    print("sts_sender started")
    while True:
        chunk = await audio_queue.get()
        await sts_ws.send(chunk)

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

@app.post("/incoming-call")
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML to connect to the media stream."""
    host = request.url.hostname
    # If running locally with ngrok, the host might be localhost in some headers, 
    # but we need the public ngrok URL. 
    # However, Twilio sends the request to the ngrok URL, so request.url.hostname should be correct 
    # IF the proxy headers are handled correctly. 
    # For safety, let's try to grab the Host header.
    host = request.headers.get("host", host)
    
    response = f"""<Response>
    <Connect>
        <Stream url="wss://{host}/media-stream" />
    </Connect>
</Response>"""
    return HTMLResponse(content=response, media_type="application/xml")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)