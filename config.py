import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

CHAT_MODEL = "llama-3.3-70b-versatile"

DB_PATH = "data/bot.db"
CHROMA_PATH = "data/chroma"

MAX_CHUNKS_PER_QUERY = 5
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

FREE_MESSAGES_PER_DAY = 20
MAX_FAQ_ITEMS = 50
