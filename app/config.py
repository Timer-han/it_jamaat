import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    DATABASE_URL: str = os.getenv('DATABASE_URL')

config = Config()