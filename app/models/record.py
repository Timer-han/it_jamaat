from sqlalchemy import Column, Integer, String
from app.utils.db import Base

class Record(Base):
    __tablename__ = 'records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    file_url = Column(String(500), nullable=False)

    def __repr__(self):
        return f"<Record(id={self.id}, title='{self.title}')>"