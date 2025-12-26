from perplexity import Perplexity
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Perplexity Library...")

# Note: The user's snippet didn't use an API key, but the library might need one or use a different auth method.
# Let's try exactly as user posted first.
try:
    client = Perplexity()
    
    # Search for results from a specific country
    search = client.search.create(
        query="NBA Lakers vs Warriors latest news injuries",
        country="US",  # ISO country code
        max_results=3
    )
    
    for result in search.results:
        print(f"✅ Found: {result.title}: {result.url}")
        
except Exception as e:
    print(f"❌ Error: {e}")
