import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("DEEPGRAM_API_KEY")
if key:
    print(f"DEEPGRAM_API_KEY found: {key[:5]}...")
else:
    print("DEEPGRAM_API_KEY NOT found")
