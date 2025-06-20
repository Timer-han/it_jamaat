from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Vacancy(Base):
    __tablename__ = 'vacancies'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000))
    link: Mapped[str] = mapped_column(String(300), nullable=False)