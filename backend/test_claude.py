import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

key = os.getenv("CLAUDE_API_KEY")
print(f"Key loaded: {key[:10]}...{key[-5:] if key else 'None'}")

try:
    client = Anthropic(api_key=key)
    print("Client initialized. Sending request...")
    
    resp = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello via API"}]
    )
    print(f"✅ Success: {resp.content[0].text}")
except Exception as e:
    print(f"❌ Error: {e}")
