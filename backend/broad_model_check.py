from google import genai
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

load_dotenv()

def test_gemini():
    print("\n[Gemini] Checking available models...")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    try:
        # Check a few likely ones
        for m in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
            try:
                client.models.generate_content(model=m, contents="ping")
                print(f"✅ {m} is available")
            except:
                print(f"❌ {m} failed")
    except Exception as e:
        print(f"Error: {e}")

def test_claude():
    print("\n[Claude] Checking available models...")
    client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    for m in ["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620", "claude-3-haiku-20240307"]:
        try:
            client.messages.create(model=m, max_tokens=10, messages=[{"role": "user", "content": "hi"}])
            print(f"✅ {m} is available")
        except Exception as e:
            print(f"❌ {m} failed")

def test_openai():
    print("\n[OpenAI] Checking available models...")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    for m in ["gpt-4o", "gpt-4o-mini"]:
        try:
            client.chat.completions.create(model=m, messages=[{"role": "user", "content": "hi"}], max_tokens=10)
            print(f"✅ {m} is available")
        except Exception as e:
            print(f"❌ {m} failed")

    test_openai()

    print("\n[Perplexity] Checking available models...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")
        for m in ["sonar", "sonar-deep-research"]:
            try:
                client.chat.completions.create(model=m, messages=[{"role": "user", "content": "hi"}], max_tokens=10)
                print(f"✅ {m} is available")
            except Exception as e:
                print(f"❌ {m} failed: {e}")
    except Exception as e:
        print(f"Perplexity Error: {e}")
