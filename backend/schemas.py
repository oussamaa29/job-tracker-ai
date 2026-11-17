from datetime import date, datetime
from typing import Literal, Optional, List, get_args

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["to_apply", "applied", "phone_screen", "interview", "offer", "rejected", "withdrawn"]
STATUSES = list(get_args(Status))


class ApplicationBase(BaseModel):
    company: str
    position: str
    status: Status = "to_apply"
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    source: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None
    job_description: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[Status] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    source: Optional[str] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None
    job_description: Optional[str] = None


class ApplicationOut(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_score: Optional[float] = None
    match_keywords_matched: Optional[str] = None
    match_keywords_missing: Optional[str] = None
    match_suggestions: Optional[str] = None
    match_reasoning: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cv_text: Optional[str] = None


class ProfileUpdate(BaseModel):
    cv_text: str


class MatchRequest(BaseModel):
    job_description: Optional[str] = None
    cv_text: Optional[str] = None


class MatchResult(BaseModel):
    match_score: float = Field(ge=0, le=100)
    keywords_matched: List[str]
    keywords_missing: List[str]
    suggestions: List[str]
    reasoning: str


class StatsOut(BaseModel):
    total: int
    by_status: dict
