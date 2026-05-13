import os
from google import genai
import dotenv
from pathlib import Path

#  Load the .env file from the 02_backend folder
env_path = Path(__file__).parent.parent / '02_backend' / '.env'
dotenv.load_dotenv(dotenv_path=env_path)

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

print("Available models that support embedContent:")
for m in client.models.list():
    # Filter for models that can embed
    if 'embedContent' in m.supported_actions:
        print(f"  {m.name}")