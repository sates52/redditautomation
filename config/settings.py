import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WORD_FILES_DIR = DATA_DIR / "word_files"
DB_PATH = DATA_DIR / "reddit_automation.db"

load_dotenv(BASE_DIR / ".env")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

SUBREDDIT_1 = os.getenv("SUBREDDIT_1", "KonusarakOgren")
SUBREDDIT_2 = os.getenv("SUBREDDIT_2", "IngilizceKonusma")

POSTS_PER_DAY = int(os.getenv("POSTS_PER_DAY", "5"))
MIN_HOURS_BETWEEN_POSTS = int(os.getenv("MIN_HOURS_BETWEEN_POSTS", "2"))
DAILY_POST_LIMIT = int(os.getenv("DAILY_POST_LIMIT", "5"))
TARGET_SUBREDDIT = os.getenv("TARGET_SUBREDDIT", "KonusarakOgren")

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct" # Updated to a more efficient model for this task
