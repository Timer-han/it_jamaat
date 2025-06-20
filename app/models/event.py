from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Event(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000))
    datetime: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    category: Mapped[str] = mapped_column(String(100))
    mentor_id: Mapped[int] = mapped_column(ForeignKey('mentors.id'))
    mentor: Mapped['Mentor'] = relationship('Mentor', back_populates='events')