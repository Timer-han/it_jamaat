from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    datetime = Column(DateTime, nullable=False)
    category = Column(String(100), nullable=True)
    mentor_id = Column(Integer, ForeignKey('mentors.id'), nullable=False)

    mentor = relationship('Mentor', back_populates='events')

    def __repr__(self):
        return (
            f"<Event(id={self.id}, title='{self.title}', datetime={self.datetime})>"
        )