import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# Load local environment variables from .env
load_dotenv()

# Get key
api_key = os.getenv("GEMINI_API_KEY")

print("==============================================")
print("       Gemini API Connection Test             ")
print("==============================================")

if not api_key:
    print("[FAIL] GEMINI_API_KEY is not set in your .env file.")
    print("Please make sure you have a .env file with: GEMINI_API_KEY=your_key_here")
    exit(1)

print(f"Key loaded: {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else ''}")
print("Configuring GenAI client...")

try:
    # Initialize client using the same robust method as the agents
    from agents.base import get_gemini_client
    client = get_gemini_client()
    
    print("Sending test request to Gemini...")
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents="Say hello and confirm you are online!"
    )
    
    print("\n[SUCCESS] Response from Gemini:")
    print("----------------------------------------------")
    print(response.text.strip())
    print("----------------------------------------------")
    
except APIError as e:
    print(f"\n[FAIL] Gemini API Error: {e}")
except Exception as e:
    print(f"\n[FAIL] General Error: {e}")
    print("Make sure you have run: pip install google-genai python-dotenv")

print("==============================================")
