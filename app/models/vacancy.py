from sqlalchemy import Column, Integer, String, Text
from app.utils.db import Base

class Vacancy(Base):
    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String(500), nullable=False)

    def __repr__(self):
        return f"<Vacancy(id={self.id}, title='{self.title}')>"