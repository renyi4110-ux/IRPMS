# 科研项目进展智能管理与汇报系统（RPIS）

本仓库提供一个“精简但完整”的 RPIS Demo，包含 FastAPI 后端、React 前端与 SQLite 数据库，覆盖需求文档里提到的核心模块：

* 数据收集、任务计划导入、日志解析
* 任务状态更新、风险与指标统计
* 报告生成、系统通知
* Web 控制台展示项目概况、任务列表、报告与通知

## 目录结构

```
backend/          # FastAPI 应用及业务逻辑
  app/
    main.py       # 接口路由
    models.py     # SQLAlchemy 模型
    services.py   # 任务解析、报告生成等服务
    utils.py      # 文本解析、规则逻辑
    database.py   # SQLite 初始化
frontend/         # Vite + React 前端
  src/App.jsx     # 单页控制台
  src/styles.css  # 样式
README.md
```

## 快速启动

1. **启动后端**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2. **启动前端**

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

前端默认通过 Vite 代理把 `/api` 请求转发到 `http://localhost:8000`。

## 使用说明

1. 在前端控制台创建项目并导入任务计划表（支持 CSV/XLSX，需包含「任务名称、负责人、计划开始/结束时间」列）。
2. 上传日志或会议纪要（支持 txt/md/docx）：系统自动拆分记录并基于规则/LLM 替代逻辑提取任务进展、问题与风险。
3. 进入「报告中心」点击“生成报告”，即可得到 Markdown 周报草稿。
4. 在“系统通知”中查看日志解析、风险提示与报告生成提醒。

SQLite 数据库默认保存在 `backend/app.db`，可直接删除重新初始化。若要接入真实 LLM，可在 `app/services.py` / `app/utils.py` 中替换现有规则逻辑。
