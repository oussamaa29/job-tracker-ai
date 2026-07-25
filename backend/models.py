from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date

from database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    position = Column(String, nullable=False)
    status = Column(String, nullable=False, default="to_apply")
    job_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    source = Column(String, nullable=True)
    applied_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    job_description = Column(Text, nullable=True)

    match_score = Column(Float, nullable=True)
    match_keywords_matched = Column(Text, nullable=True)
    match_keywords_missing = Column(Text, nullable=True)
    match_suggestions = Column(Text, nullable=True)
    match_reasoning = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Profile(Base):
    __tablename__ = "profile"

    id = Column(Integer, primary_key=True, index=True)
    cv_text = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
