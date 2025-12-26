from google import genai
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

load_dotenv()

print("--- 2025 Model Connectivity Check ---")

# 1. Gemini 3
print("\nTesting Gemini 3 (gemini-3-pro)...")
try:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(model="gemini-3-pro", contents="ping")
    print(f"✅ Gemini 3 Success: {response.text[:50]}...")
except Exception as e:
    print(f"❌ Gemini 3 Failed: {e}")

# 2. Claude 4.5
print("\nTesting Claude 4.5 (claude-4-5-sonnet-20250929)...")
try:
    client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    message = client.messages.create(
        model="claude-4-5-sonnet-20250929",
        max_tokens=10,
        messages=[{"role": "user", "content": "hi"}]
    )
    print(f"✅ Claude 4.5 Success: {message.content[0].text}...")
except Exception as e:
    print(f"❌ Claude 4.5 Failed: {e}")

# 3. GPT-5
print("\nTesting GPT-5 (gpt-5.2)...")
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=10
    )
    print(f"✅ GPT-5 Success: {response.choices[0].message.content}...")
except Exception as e:
    print(f"❌ GPT-5 Failed: {e}")

# 4. Perplexity Deep Research
print("\nTesting Perplexity Deep Research (sonar-deep-research)...")
try:
    client = OpenAI(api_key=os.getenv("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model="sonar-deep-research",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=10
    )
    print(f"✅ Perplexity Success: {response.choices[0].message.content}...")
except Exception as e:
    print(f"❌ Perplexity Failed: {e}")
