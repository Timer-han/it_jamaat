from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from app.utils.db import Base

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_roles = Column(ARRAY(String), nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', active={self.is_active})>"