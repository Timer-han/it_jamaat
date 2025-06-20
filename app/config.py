import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMINS: set[int] = set(map(int, os.getenv('ADMINS', '').split(',')))
    SQLALCHEMY_URL: str = os.getenv('SQLALCHEMY_URL')

config = Config()