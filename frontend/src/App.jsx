import { useEffect, useMemo, useState } from 'react';

const API_BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || '请求失败');
  }
  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return res.json();
  }
  return res.text();
}

function ProjectForm({ onCreated }) {
  const [form, setForm] = useState({ name: '', description: '', start_date: '', end_date: '' });
  const handleChange = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = { ...form };
    if (!payload.name.trim()) return;
    const data = await request('/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    setForm({ name: '', description: '', start_date: '', end_date: '' });
    onCreated(data);
  };

  return (
    <form className="section-card" onSubmit={handleSubmit}>
      <h2>创建新项目</h2>
      <div className="form-grid">
        <input placeholder="项目名称" value={form.name} onChange={(e) => handleChange('name', e.target.value)} />
        <input placeholder="开始日期" type="date" value={form.start_date} onChange={(e) => handleChange('start_date', e.target.value)} />
        <input placeholder="结束日期" type="date" value={form.end_date} onChange={(e) => handleChange('end_date', e.target.value)} />
      </div>
      <textarea placeholder="项目简介" value={form.description} onChange={(e) => handleChange('description', e.target.value)} />
      <button className="primary" type="submit">创建</button>
    </form>
  );
}

function FileUploader({ projectId, onUploaded }) {
  const [category, setCategory] = useState('日志');
  const [file, setFile] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    const data = await request(`/projects/${projectId}/upload`, {
      method: 'POST',
      body: formData
    });
    setFile(null);
    onUploaded(data.message);
  };

  return (
    <form className="section-card" onSubmit={handleUpload}>
      <h2>上传文件</h2>
      <div className="form-grid">
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="日志">日志文件</option>
          <option value="会议纪要">会议纪要</option>
          <option value="任务计划表">任务计划表</option>
        </select>
        <input type="file" onChange={(e) => setFile(e.target.files?.[0])} />
      </div>
      <button className="primary" type="submit">开始解析</button>
    </form>
  );
}

function MetricsCard({ metrics }) {
  if (!metrics) return null;
  return (
    <div className="section-card">
      <h2>项目总览</h2>
      <p>{metrics.summary}</p>
      <div className="form-grid">
        <div>总任务：{metrics.total_tasks}</div>
        <div>完成：{metrics.completed_tasks}</div>
        <div>进行中：{metrics.in_progress_tasks}</div>
        <div>存在问题：{metrics.issue_tasks}</div>
        <div>风险任务：{metrics.risk_tasks}</div>
        <div>超期：{metrics.overdue_tasks}</div>
        <div>完成率：{(metrics.completion_rate * 100).toFixed(0)}%</div>
      </div>
    </div>
  );
}

function TaskTable({ tasks }) {
  if (!tasks.length) {
    return <div className="section-card">暂无任务</div>;
  }
  return (
    <div className="section-card">
      <h2>任务列表</h2>
      <table className="list-table">
        <thead>
          <tr>
            <th>任务</th>
            <th>负责人</th>
            <th>状态</th>
            <th>计划结束</th>
            <th>风险</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.id}>
              <td>
                <div>{task.name}</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>{task.summary}</div>
              </td>
              <td>{task.owner}</td>
              <td>
                <span className={`tag ${task.status === '已完成' ? 'success' : ''}`}>{task.status}</span>
                {task.has_issue && <span className="tag danger">有问题</span>}
              </td>
              <td>{task.plan_end || '-'}</td>
              <td>
                {task.risk_flag === '存在风险' ? (
                  <span className="tag danger">存在风险</span>
                ) : (
                  <span className="tag">正常</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Notifications({ notifications, onRead }) {
  return (
    <div className="section-card">
      <h2>系统通知</h2>
      <div className="notifications">
        {notifications.map((item) => (
          <div key={item.id} style={{ borderBottom: '1px solid #e5e7eb', padding: '8px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>{item.message}</strong>
              {!item.is_read && (
                <button className="primary" style={{ padding: '2px 8px' }} onClick={() => onRead(item.id)}>
                  标记已读
                </button>
              )}
            </div>
            <small>{new Date(item.created_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function Reports({ projectId, reports, onCreated }) {
  const [title, setTitle] = useState('本周周报');

  const handleGenerate = async () => {
    const formData = new FormData();
    formData.append('title', title);
    const report = await request(`/projects/${projectId}/reports`, {
      method: 'POST',
      body: formData
    });
    onCreated(report);
  };

  return (
    <div className="section-card">
      <h2>报告中心</h2>
      <div className="form-grid">
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="报告标题" />
        <button type="button" className="primary" onClick={handleGenerate}>
          生成报告
        </button>
      </div>
      {reports.map((report) => (
        <div key={report.id} style={{ marginTop: 16 }}>
          <h3>{report.title}</h3>
          <small>{new Date(report.created_at).toLocaleString()}</small>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f9fafb', padding: 12 }}>{report.content}</pre>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [projects, setProjects] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [reports, setReports] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    request('/projects').then(setProjects);
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    request(`/projects/${selectedId}/tasks`).then(setTasks);
    request(`/projects/${selectedId}/metrics`).then(setMetrics);
    request(`/projects/${selectedId}/notifications`).then(setNotifications);
    request(`/projects/${selectedId}/reports`).then(setReports);
  }, [selectedId]);

  const currentProject = useMemo(() => projects.find((p) => p.id === selectedId), [projects, selectedId]);

  const handleProjectCreated = (project) => {
    setProjects((prev) => [project, ...prev]);
    setSelectedId(project.id);
  };

  const handleNotificationRead = async (id) => {
    await request(`/projects/${selectedId}/notifications/${id}/read`, { method: 'POST' });
    setNotifications((prev) => prev.map((item) => (item.id === id ? { ...item, is_read: true } : item)));
  };

  const handleReportCreated = (report) => {
    setReports((prev) => [report, ...prev]);
  };

  const handleUploaded = (msg) => {
    setMessage(msg);
    request(`/projects/${selectedId}/tasks`).then(setTasks);
    request(`/projects/${selectedId}/metrics`).then(setMetrics);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>RPIS 控制台</h1>
        {projects.map((project) => (
          <button key={project.id} onClick={() => setSelectedId(project.id)} style={{ background: selectedId === project.id ? '#1d4ed8' : '#2563eb' }}>
            {project.name}
          </button>
        ))}
        <p style={{ fontSize: 12, color: '#9ca3af' }}>共 {projects.length} 个项目</p>
      </aside>
      <main className="main-panel">
        <ProjectForm onCreated={handleProjectCreated} />
        {currentProject ? (
          <>
            <MetricsCard metrics={metrics} />
            <FileUploader projectId={currentProject.id} onUploaded={handleUploaded} />
            {message && <div className="section-card">{message}</div>}
            <TaskTable tasks={tasks} />
            <Reports projectId={currentProject.id} reports={reports} onCreated={handleReportCreated} />
            <Notifications notifications={notifications} onRead={handleNotificationRead} />
          </>
        ) : (
          <div className="section-card">请选择一个项目以查看详情</div>
        )}
      </main>
    </div>
  );
}
