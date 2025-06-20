from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import config

# Создаём движок
engine = create_engine(config.DATABASE_URL, echo=False)
# Сессия
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Базовый класс для моделей
Base = declarative_base()

# Импорт моделей, чтобы ORM-зависимости были зарегистрированы
import app.models.mentor  # noqa: F401
import app.models.event   # noqa: F401
import app.models.record  # noqa: F401
import app.models.project # noqa: F401
import app.models.vacancy # noqa: F401