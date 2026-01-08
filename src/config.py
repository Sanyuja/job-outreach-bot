import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Export the key so other modules can import it
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
