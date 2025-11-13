import asyncio  #Enables asynchronous operations — perfect for handling live, real-time communication
import base64  #Used to encode/decode audio data audio to text format for transmission
import json   #Used to load or parse your config.json file
import websockets #library for connecting to Deepgram’s
import os  #Lets you access system environment variables like your API keys.
from dotenv import load_dotenv #Loads environment variables from a .env file

load_dotenv()        #line loads your .env file

def sts_connect():
  api_key = os.getenv("DEEPGRAM_API_KEY")
  if not api_key:
    raise Exception("DEEPGRAM_API_KEY is not found")
  
  sts_ws = websockets.connect(
      uri="wss://agent.deepgram.com/v1/agent/converse",
      subprotocols = ["token", api_key]
  )
  return sts_ws

def load_config():
  with open("config.json" , "r") as f:
    return json.load(f)
  
#async def, which means they run asynchronously — multiple things can happen at the same time.
#async / WebSocket server part of your voice agent — the part that connects everything (Twilio, Deepgram, and your AI logic) and handles the real-time conversation pipeline.
#Twilio → Deepgram → GPT → Deepgram → Twilio
#(Listen → Think → Speak → Respond)
async def handle_barge_in(decoded, twilio_ws , streamsid):
  pass

async def handel_text_message(decoded ,  twilio_ws , streamsid):
  pass

async def sts_sender(sts_ws , audio_queue):
  pass

async def sts_receiver(sts_ws , twilio_ws , streamsid_queue):
  pass

async def twilio_handler(twilio_ws):
  pass

async def main():
    await websockets.serve(twilio_handler, host="localhost", port=5000)
    print("started server")
    await asyncio.Future()  # run forever

if __name__ == "__main__":
  asyncio.run(main())