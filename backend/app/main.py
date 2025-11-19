from __future__ import annotations

import os
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .services import (
    calculate_metrics,
    create_project,
    generate_report,
    import_task_plan,
    process_text_file,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="科研项目进展智能管理与汇报系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/projects", response_model=schemas.ProjectResponse)
def create_project_endpoint(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return create_project(db, project.model_dump())


@app.get("/projects", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).order_by(models.Project.created_at.desc()).all()


@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/projects/{project_id}/tasks", response_model=List[schemas.TaskResponse])
def list_tasks(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Task).filter(models.Task.project_id == project_id).all()


@app.get("/projects/{project_id}/logs", response_model=List[schemas.LogResponse])
def list_logs(project_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.LogRecord)
        .filter(models.LogRecord.project_id == project_id)
        .order_by(models.LogRecord.created_at.desc())
        .all()
    )


@app.post("/projects/{project_id}/upload")
def upload_file(
    project_id: int,
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    content = file.file.read()
    if category == "任务计划表":
        count = import_task_plan(db, project, content, file.filename)
        return {"message": f"成功导入 {count} 条任务计划"}
    else:
        records, updated_tasks = process_text_file(db, project, content, file.filename, category)
        return {"message": f"解析 {records} 条记录，更新 {updated_tasks} 个任务"}


@app.get("/projects/{project_id}/metrics", response_model=schemas.MetricsResponse)
def get_metrics(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return calculate_metrics(db, project_id)


@app.post("/projects/{project_id}/reports", response_model=schemas.ReportResponse)
def create_report(project_id: int, title: str = Form(...), db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return generate_report(db, project, title)


@app.get("/projects/{project_id}/reports", response_model=List[schemas.ReportResponse])
def list_reports(project_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Report)
        .filter(models.Report.project_id == project_id)
        .order_by(models.Report.created_at.desc())
        .all()
    )


@app.get("/projects/{project_id}/notifications", response_model=List[schemas.NotificationResponse])
def list_notifications(project_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Notification)
        .filter(models.Notification.project_id == project_id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@app.post("/projects/{project_id}/notifications/{notification_id}/read")
def mark_notification_read(project_id: int, notification_id: int, db: Session = Depends(get_db)):
    notification = db.get(models.Notification, notification_id)
    if not notification or notification.project_id != project_id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"message": "已标记为已读"}
