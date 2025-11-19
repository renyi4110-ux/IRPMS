from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class TaskBase(BaseModel):
    name: str
    owner: Optional[str] = None
    plan_start: Optional[date] = None
    plan_end: Optional[date] = None


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    status: str
    summary: str
    has_issue: bool
    issue_text: str
    is_overdue: bool
    risk_flag: str

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    id: int
    content: str
    category: str
    source_file: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MetricsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    issue_tasks: int
    risk_tasks: int
    completion_rate: float
    summary: str
    overdue_tasks: int
