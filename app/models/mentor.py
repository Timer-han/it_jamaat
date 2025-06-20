from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Mentor(Base):
    __tablename__ = 'mentors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    contact = Column(String(255), nullable=True)

    events = relationship('Event', back_populates='mentor')

    def __repr__(self):
        return f"<Mentor(id={self.id}, name='{self.name}')>"