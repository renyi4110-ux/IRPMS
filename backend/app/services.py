from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from . import models
from .utils import (
    analyze_records,
    build_summary,
    create_notification_message,
    load_text_from_file,
    parse_task_plan,
    parse_text_records,
    plan_record_to_task,
)


def create_project(db: Session, data: Dict[str, str]) -> models.Project:
    project = models.Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def add_notification(db: Session, project_id: int, kind: str, payload: Dict[str, str]) -> models.Notification:
    message = create_notification_message(kind, payload)
    notification = models.Notification(project_id=project_id, type=kind, message=message)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def import_task_plan(db: Session, project: models.Project, file_bytes: bytes, filename: str) -> int:
    records = parse_task_plan(file_bytes, filename)
    count = 0
    for record in records:
        task_data = plan_record_to_task(record)
        task = models.Task(
            project_id=project.id,
            name=task_data["name"],
            owner=task_data.get("owner") or "未指定",
            plan_start=task_data.get("plan_start"),
            plan_end=task_data.get("plan_end"),
        )
        db.add(task)
        count += 1
    db.commit()
    return count


def _ensure_task(db: Session, project: models.Project, name: str, owner: str) -> models.Task:
    task = (
        db.query(models.Task)
        .filter(models.Task.project_id == project.id, models.Task.name == name)
        .first()
    )
    if task:
        if owner and owner != "未指定":
            task.owner = owner
        return task
    task = models.Task(project_id=project.id, name=name, owner=owner or "未指定")
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def process_text_file(
    db: Session, project: models.Project, file_bytes: bytes, filename: str, category: str
) -> Tuple[int, int]:
    text = load_text_from_file(file_bytes, filename)
    records = parse_text_records(text)
    tasks = [task.name for task in project.tasks]
    extracted = analyze_records(records, tasks)
    updated_tasks = set()
    for record_text, payload in zip(records, extracted):
        task = _ensure_task(db, project, payload["task_name"], payload["owner"])
        log = models.LogRecord(
            project_id=project.id,
            task_id=task.id,
            source_file=filename,
            category=category,
            content=record_text,
        )
        db.add(log)
        task.summary = build_summary([log.content for log in task.logs] + [record_text])
        task.status = payload["status"]
        if payload["has_issue"]:
            task.has_issue = True
            task.issue_text = payload["issue_text"]
        updated_tasks.add(task.id)
    db.commit()
    _update_task_risks(db, project.id)
    db.commit()
    return len(records), len(updated_tasks)


def _update_task_risks(db: Session, project_id: int) -> None:
    today = date.today()
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    risk_tasks = 0
    for task in tasks:
        overdue = False
        if task.plan_end and task.status != "已完成" and today > task.plan_end:
            overdue = True
        task.is_overdue = overdue
        if task.has_issue or task.is_overdue:
            task.risk_flag = "存在风险"
            risk_tasks += 1
        elif task.status == "已完成":
            task.risk_flag = "正常"
        else:
            task.risk_flag = "正常"
    db.commit()
    if risk_tasks:
        add_notification(db, project_id, "risk", {"risk_tasks": risk_tasks})


def calculate_metrics(db: Session, project_id: int) -> Dict[str, str]:
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.status == "已完成"])
    in_progress = len([t for t in tasks if t.status != "已完成" and t.status != "未开始"])
    issues = len([t for t in tasks if t.has_issue])
    risk = len([t for t in tasks if t.risk_flag == "存在风险"])
    overdue = len([t for t in tasks if t.is_overdue])
    completion_rate = round(completed / total, 2) if total else 0.0
    summary = f"当前共有 {total} 个任务，完成 {completed} 个，{risk} 个存在风险。"
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "issue_tasks": issues,
        "risk_tasks": risk,
        "overdue_tasks": overdue,
        "completion_rate": completion_rate,
        "summary": summary,
    }


def generate_report(db: Session, project: models.Project, title: str) -> models.Report:
    tasks = db.query(models.Task).filter(models.Task.project_id == project.id).all()
    completed = [t for t in tasks if t.status == "已完成"]
    in_progress = [t for t in tasks if t.status == "进行中"]
    risky = [t for t in tasks if t.risk_flag == "存在风险"]
    pending = [t for t in tasks if t.status == "未开始"]

    def render_task_list(task_list: List[models.Task]) -> str:
        if not task_list:
            return "- 暂无\n"
        lines = [f"- {task.name}（负责人：{task.owner}，状态：{task.status}）" for task in task_list]
        return "\n".join(lines) + "\n"

    content = f"""# {title}

## 项目概况
- 项目名称：{project.name}
- 周期：{project.start_date} ~ {project.end_date}
- 任务总数：{len(tasks)}
- 完成率：{calculate_metrics(db, project.id)['completion_rate'] * 100:.0f}%

## 本周期完成的任务
{render_task_list(completed)}
## 进行中的关键任务
{render_task_list(in_progress)}
## 存在问题与风险
{render_task_list(risky)}
## 下周期建议计划
{render_task_list(pending or in_progress)}
"""
    report = models.Report(project_id=project.id, title=title, content=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    add_notification(db, project.id, "report", {"title": title})
    return report
