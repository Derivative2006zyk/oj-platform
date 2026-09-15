# OJ Platform

多端互通模块化开源刷题系统 - 0.1 版本（题库中心）

## 功能

- 多题型题目管理：算法题、选择题、填空题、证明题、科研项目
- 主分类目录：算法、数学、物理、英语、其他
- 图片上传（除选择题和填空题外均支持）
- 题目列表、详情、查看答案
- 管理员密钥保护录入/编辑/删除

## 技术栈

### 后端

- FastAPI 0.115
- PostgreSQL 15
- SQLAlchemy 2.0 (async)
- Alembic
- Pytest

### 前端

- Vue 3
- Vite 5
- TypeScript
- Vue Router 4
- Axios
- Marked + highlight.js

## 快速开始

### 前置要求

- Docker Desktop
- Node.js 18+
- Python 3.11（本地开发用，容器部署可跳过）

### 启动后端（Docker）

```bash
cd E:\github_project\oj-platform
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

后端服务：http://localhost:8000

API 文档：http://localhost:8000/docs

### 启动前端（开发模式）

```bash
cd frontend
npm install
npm run dev
```

前端页面：http://localhost:5173

### 管理员密钥

默认密钥：`admin-key-change-me`

通过环境变量 `ADMIN_KEY` 修改：

```bash
cp .env.example .env
# 编辑 .env，修改 ADMIN_KEY
```

## 项目结构

```
oj-platform/
├── backend/
│   ├── app/
│   │   ├── core/           # 配置和鉴权
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic 模型
│   │   ├── plugins/        # 业务插件
│   │   │   └── problem_plugin/
│   │   │       ├── api.py
│   │   │       ├── service.py
│   │   │       └── image_api.py
│   │   ├── database.py
│   │   └── main.py
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 测试
│   ├── uploads/            # 图片存储
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # API 封装
│   │   ├── components/     # 通用组件
│   │   ├── router/         # 路由
│   │   ├── utils/          # 工具
│   │   └── views/          # 页面
│   └── vite.config.ts
├── docs/
│   └── learning-log/       # 学习日志
├── docker-compose.yml
├── .env.example
└── README.md
```

## API 概览

### 公共接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/categories | 分类列表 |
| GET | /api/problems | 题目列表（支持分页筛选） |
| GET | /api/problems/{id} | 题目详情 |
| GET | /api/problems/{id}/answer | 查看答案 |
| GET | /api/tags | 所有标签 |
| GET | /api/images/{id} | 访问图片 |

### 管理员接口（需要 X-Admin-Key）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/admin/problems | 创建题目 |
| PUT | /api/admin/problems/{id} | 更新题目 |
| DELETE | /api/admin/problems/{id} | 删除题目 |
| POST | /api/admin/images | 上传图片 |

## 测试

```bash
cd backend
pytest tests/ -v
```

## 数据库迁移

```bash
# 在 backend 目录下
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic downgrade -1
```

## 部署

### 完整容器化部署

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

## 许可证

MIT