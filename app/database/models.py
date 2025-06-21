from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Связующая таблица для проектов и специальностей
project_skills = Table('project_skills', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('skill', String(50))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    full_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_mentor = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Mentor(Base):
    __tablename__ = 'mentors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100), nullable=False)
    bio = Column(Text)
    specialization = Column(String(100))
    contact_info = Column(String(200))
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", backref="mentor_profile")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))  # lecture, meeting, seminar
    mentor_id = Column(Integer, ForeignKey('mentors.id'))
    date_time = Column(DateTime, nullable=False)
    location = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    mentor = relationship("Mentor", backref="events")
    creator = relationship("User", backref="created_events")

class Lecture(Base):
    __tablename__ = 'lectures'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    mentor_id = Column(Integer, ForeignKey('mentors.id'))
    file_path = Column(String(500))
    video_url = Column(String(500))
    duration = Column(Integer)  # в минутах
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    
    mentor = relationship("Mentor", backref="lectures")
    uploader = relationship("User", backref="uploaded_lectures")

class Vacancy(Base):
    __tablename__ = 'vacancies'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    company = Column(String(100))
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String(100))
    location = Column(String(100))
    contact_info = Column(String(200))
    is_active = Column(Boolean, default=True)
    posted_at = Column(DateTime, default=datetime.utcnow)
    posted_by = Column(Integer, ForeignKey('users.id'))
    
    poster = relationship("User", backref="posted_vacancies")

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='discussion')  # discussion, development, completed
    required_skills = Column(Text)  # JSON строка со списком навыков
    contact_person = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    contact = relationship("User", backref="managed_projects")