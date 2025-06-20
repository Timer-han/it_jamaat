from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Mentor(Base):
    __tablename__ = 'mentors'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str] = mapped_column(String(1000))
    contact: Mapped[str] = mapped_column(String(100))
    events: Mapped[list['Event']] = relationship('Event', back_populates='mentor')