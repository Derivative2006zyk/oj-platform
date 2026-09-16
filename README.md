# OJ Platform

多端互通模块化开源刷题系统 - 0.1 版本（题库中心）

## 简介

一个面向多题型的题库管理系统，支持算法题、选择题、填空题、证明题、科研项目五种题型，提供分类导航、多维度筛选、图片上传、Markdown 渲染与代码高亮等功能。

前后端分离，后端 FastAPI + PostgreSQL，前端 Vue3 + Vite + TypeScript，提供 Docker Compose 一键部署。

## 功能

- 五种题型：算法题、选择题、填空题、证明题、科研项目
- 主分类导航：算法、数学、物理、英语、其他
- 多维度筛选：分类、难度、标签、题型、关键词
- 分页与 URL 同步：筛选条件写入 URL，可分享与刷新保留
- 题目详情：五种题型差异化渲染，Markdown + 代码高亮
- 图片上传：除选择题和填空题外均支持
- 管理员密钥保护录入、编辑、删除

## 技术栈

### 后端

| 组件 | 版本 | 用途 |
|---|---|---|
| FastAPI | 0.115 | Web 框架 |
| Uvicorn | 0.30 | ASGI 服务器 |
| SQLAlchemy | 2.0 (async) | ORM |
| asyncpg | 0.31 | PostgreSQL 异步驱动 |
| Alembic | 1.13 | 数据库迁移 |
| Pydantic | 2.x | 数据校验 |
| Pillow | 10.x | 图片校验 |
| Pytest | 8.x | 测试框架 |

### 前端

| 组件 | 版本 | 用途 |
|---|---|---|
| Vue | 3.5 | 前端框架 |
| Vite | 5.x | 构建工具 |
| TypeScript | 5.x | 类型系统 |
| Vue Router | 4.x | 路由 |
| Axios | 1.x | HTTP 客户端 |
| Marked | 12.x | Markdown 渲染 |
| highlight.js | 11.x | 代码高亮 |

### 部署

- Docker Desktop
- Docker Compose
- Nginx（生产环境反向代理）

## 前置要求

- Docker Desktop
- Node.js 18 及以上
- Python 3.11（本地开发使用；容器部署可跳过）

## 快速开始

### 方式一：完全容器化后端 + 本地前端开发

**第一步：启动后端与数据库**

```bash
cd oj-platform
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

后端服务：http://localhost:8000

API 文档：http://localhost:8000/docs

**第二步：启动前端开发服务器**

```bash
cd frontend
npm install
npm run dev
```

前端页面：http://localhost:5173

开发模式下，Vite 通过代理把 `/api` 请求转发到后端 8000。

### 方式二：本地后端 + Docker 数据库

只需数据库用容器，后端在本地跑，便于调试：

```bash
# 只启动数据库
docker compose up -d postgres

# 本地启动后端（新终端）
conda activate oj
cd backend
uvicorn app.main:app --reload --port 8000

# 启动前端（另一个终端）
cd frontend
npm run dev
```

### 方式三：前端预览打包产物

验证生产构建结果：

```bash
cd frontend
npm run build
npm run preview
```

预览地址：http://localhost:4173

`vite.config.ts` 中已配置 `preview.proxy`，`/api` 请求会转发到后端 8000。

## 管理员密钥

默认密钥：`admin-key-change-me`

修改方式：

```bash
cp .env.example .env
# 编辑 .env，修改 ADMIN_KEY 的值
```

前端在录入页输入密钥后，会保存到浏览器 `localStorage`，后续请求自动携带。

## 项目结构

```
oj-platform/
├── backend/
│   ├── app/
│   │   ├── core/                       # 配置与鉴权
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/                     # SQLAlchemy 模型（5 张表）
│   │   │   ├── category.py
│   │   │   ├── problem.py
│   │   │   ├── test_case.py
│   │   │   ├── research_subproject.py
│   │   │   └── image.py
│   │   ├── schemas/                    # Pydantic 模型
│   │   │   └── problem.py
│   │   ├── plugins/                    # 业务插件
│   │   │   └── problem_plugin/
│   │   │       ├── api.py              # 路由层
│   │   │       ├── service.py          # 服务层
│   │   │       └── image_api.py        # 图片接口
│   │   ├── database.py                 # 数据库引擎与会话
│   │   └── main.py                     # 应用入口
│   ├── alembic/                        # 数据库迁移
│   ├── tests/                          # 测试
│   ├── uploads/                        # 图片存储（本地磁盘）
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                        # API 封装
│   │   │   └── problem.ts
│   │   ├── components/                 # 通用组件
│   │   │   └── MarkdownRenderer.vue
│   │   ├── router/                     # 路由配置
│   │   │   └── index.ts
│   │   ├── utils/                      # 工具
│   │   │   └── marked.ts
│   │   ├── views/                      # 页面
│   │   │   ├── ProblemList.vue
│   │   │   ├── ProblemDetail.vue
│   │   │   └── ProblemEdit.vue
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── deploy/
│   └── nginx.conf                      # 生产部署示例
├── docs/
│   └── learning-log/                   # 学习日志
├── docker-compose.yml
├── .env.example
└── README.md
```

## API 概览

### 公共接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/api/categories` | 分类列表 |
| GET | `/api/problems` | 题目列表（分页筛选） |
| GET | `/api/problems/{id}` | 题目详情 |
| GET | `/api/problems/{id}/answer` | 查看答案 |
| GET | `/api/tags` | 所有标签 |
| GET | `/api/images/{id}` | 访问图片 |

### 管理员接口

需要请求头 `X-Admin-Key: <密钥>`。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/admin/problems` | 创建题目 |
| PUT | `/api/admin/problems/{id}` | 更新题目 |
| DELETE | `/api/admin/problems/{id}` | 删除题目 |
| POST | `/api/admin/images` | 上传图片 |

### 请求参数

**题目列表** `GET /api/problems`

| 参数 | 类型 | 说明 |
|---|---|---|
| page | int | 页码，从 1 开始 |
| page_size | int | 每页条数，默认 10，最大 50 |
| category_id | int | 分类 ID |
| difficulty | int | 难度 1-5 |
| type | string | 题型 |
| tag | string | 标签 |
| keyword | string | 标题关键词 |

**题目创建** `POST /api/admin/problems`

请求体示例（算法题）：

```json
{
  "title": "两数之和",
  "category_id": 1,
  "description": "给定一个整数数组 nums 和一个目标值 target，返回两个数的下标。",
  "type": "algorithm",
  "difficulty": 1,
  "tags": ["数组", "哈希表"],
  "answer": "```python\ndef two_sum(nums, target):\n    ...\n```",
  "explanation": "使用哈希表",
  "test_cases": [
    {"input_data": "[2,7,11,15]\n9", "expected_output": "[0,1]", "is_example": true}
  ]
}
```

各题型的专属字段：

| 题型 type | 专属字段 |
|---|---|
| algorithm | test_cases |
| choice | options |
| fill_blank | blanks |
| proof | 无 |
| research | subprojects |

## 测试

```bash
cd backend
conda activate oj
pytest tests/ -v
```

预期：11 个测试全部通过。

## 数据库迁移

```bash
cd backend

# 修改模型后生成迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回退一步
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

## 部署

### 完整容器化部署

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

### 生产环境（Nginx）

1. 打包前端

```bash
cd frontend
npm run build
```

2. 把 `frontend/dist/` 内的文件上传到服务器 `/var/www/oj-platform/`

3. 使用 `deploy/nginx.conf` 作为 Nginx 配置

```bash
sudo cp deploy/nginx.conf /etc/nginx/conf.d/oj-platform.conf
sudo nginx -t
sudo systemctl reload nginx
```

Nginx 配置包含：

- 前端 history 模式回退（`try_files $uri $uri/ /index.html`）
- `/api/` 请求转发到后端 8000
- 静态资源缓存
- gzip 压缩

## 常见问题

### 容器内后端与本地 uvicorn 的选择

| 场景 | 后端运行方式 |
|---|---|
| 日常开发 | 本地 uvicorn --reload（改动立即生效） |
| 验证 Dockerfile | 容器 `docker compose up -d backend` |
| 生产部署 | 容器 + Nginx |

**注意**：容器内的代码是构建时的快照。改源码后需 `docker compose up -d --build backend` 重建，或者挂载源码目录：

```yaml
volumes:
  - ./backend/app:/app/app
```

### 图片 404 的常见原因

1. **数据库 file_path 格式不匹配**：本地 uvicorn 上传的图片路径是 Windows 绝对路径，容器内看不到。解决方案见后端 `image_api.py` 的 `get_image` 函数，兼容绝对路径、相对路径、纯文件名三种格式。

2. **上传目录未挂载**：检查 `docker-compose.yml` 中 backend 服务的 volumes 配置。

3. **Nginx 未转发 /api**：检查 `deploy/nginx.conf` 中的 `location /api/`。

### 前端接口 404

- 开发模式（5173）：检查 `vite.config.ts` 的 `server.proxy`
- 预览模式（4173）：检查 `preview.proxy`
- 生产环境：检查 Nginx 的 `location /api/`

### 修改密钥未生效

后端读环境变量，需重启服务：

```bash
docker compose restart backend
# 或本地 uvicorn 按 Ctrl+C 后重新启动
```

## 开发约定

### Git 提交规范

| 类型 | 用途 |
|---|---|
| feat | 新增功能 |
| fix | 修复 bug |
| docs | 文档 |
| test | 测试 |
| refactor | 重构 |
| chore | 杂项 |

### 数据库变更流程

1. 修改 `backend/app/models/` 下的模型
2. `alembic revision --autogenerate -m "描述"`
3. 检查生成的迁移脚本
4. `alembic upgrade head`
5. 提交迁移文件到 Git

## 已知限制

- 前端仅支持开发或预览模式，生产部署需配合 Nginx
- 图片存储为本地磁盘，多实例部署时需共享存储
- 无用户系统，管理员通过固定密钥鉴权
- 算法题暂不支持在线判题

## 后续计划

- 用户系统与权限管理
- 在线提交与判题
- 全文搜索优化
- 图片对象存储（S3 / OSS）
- 移动端适配

## 许可证

MIT