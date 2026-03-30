import os
from dotenv import load_dotenv  # type: ignore
from supabase import create_client, Client  # type: ignore

# Load .env from project root
# When running app.py from project root, this will find .env
load_dotenv(os.path.join(os.getcwd(), '.env'))

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")

if not url or not key:
    # If environment variables are already set (e.g. via shell), use them
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")

if not url or not key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY. "
                     "Check your .env file in the project root.")

# Initialize Supabase client
supabase: Client = create_client(url, key)
