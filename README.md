# OJ Platform

多端互通模块化开源刷题系统（0.2 版本进行中）

## 简介

一个面向数学与编程双场景的个人开源刷题工具，覆盖 Web、Windows、Linux、Android 四端，支持多题型题库管理、在线代码判题、实时状态推送。

后端采用 FastAPI + PostgreSQL + Redis 微内核架构，所有业务功能组织为可热插拔插件。前端 Vue3 + Vite + TypeScript，桌面端 Tauri 打包。

## 当前版本

- **0.1.0**（已发布）：题库中心，5 种题型管理 + 图片 + Markdown
- **0.2.0**（进行中）：微内核 + 用户系统 + 三语言判题 + WebSocket + 桌面端

当前进度：Day 20/28

## 功能

### 0.1 已交付

- 五种题型：算法题、选择题、填空题、证明题、科研项目
- 主分类导航：算法、数学、物理、英语、其他
- 多维度筛选：分类、难度、标签、题型、关键词
- 分页与 URL 同步
- 题目详情：五种题型差异化渲染
- 图片上传（选择题和填空题除外）
- 管理员密钥保护录入、编辑、删除

### 0.2 已完成

- **微内核架构**：路由、鉴权、事件总线、插件注册表
- **插件系统**：`@register_plugin` 装饰器，Redis Pub/Sub 事件总线，配置持久化到 PostgreSQL
- **用户系统**：注册、登录、JWT 鉴权、修改密码、个人统计
- **管理员功能**：用户列表、角色切换、封禁/解封、全局统计
- **在线判题**：
  - 三语言：Python 3.11、Java 17、C++ 17
  - Docker 沙箱隔离，资源限制（CPU、内存、进程数）
  - 结果分类：AC / WA / TLE / MLE / RE / CE
  - 异步判题（arq 队列 + Redis）
  - JVM 参数优化（`-Xmx200m`）
  - 编译缓存（Java/C++ 只编译一次）
- **实时推送**：WebSocket 推送判题状态，多端在线同步
- **提交历史**：个人提交列表、状态筛选、分页
- **代码编辑器**：Monaco Editor（VSCode 同款），按需加载三种语言，支持双向缩放
- **桌面端**：Tauri 2.x
  - 自动检测并拉起本地后端
  - 系统托盘 + 右键菜单
  - 托盘 tooltip 显示刷题统计
  - 关闭窗口最小化到托盘

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
| Redis | 5.0.8 | 事件总线、缓存、队列 |
| arq | 0.26.1 | 异步任务队列 |
| python-jose | 3.3.0 | JWT |
| passlib + bcrypt 4.0.1 | - | 密码哈希 |
| Pillow | 10.x | 图片校验 |
| Pytest | 8.x | 测试框架 |
| websockets | 13.x | WebSocket |

### 前端

| 组件 | 版本 | 用途 |
|---|---|---|
| Vue | 3.5 | 前端框架 |
| Vite | 5.x | 构建工具 |
| TypeScript | 5.x | 类型系统 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由 |
| Axios | 1.x | HTTP 客户端 |
| Monaco Editor | 0.52.2 | 代码编辑器 |
| Marked | 12.x | Markdown 渲染 |
| highlight.js | 11.x | 代码高亮 |
| MathJax | 3.x | LaTeX 公式 |

### 桌面端

| 组件 | 版本 | 用途 |
|---|---|---|
| Tauri | 2.x | 桌面壳 |
| Rust | 1.75+ | 原生逻辑 |
| reqwest | 0.12 | HTTP 客户端 |
| tauri-plugin-dialog | 2.x | 系统对话框 |

### 数据存储

| 组件 | 用途 |
|---|---|
| PostgreSQL 15 | 主数据存储 |
| Redis 7 | 事件总线、任务队列、缓存 |
| 本地磁盘 | 图片文件（`backend/uploads/`） |

### 沙箱

| 语言 | 镜像 | 大小 |
|---|---|---|
| Python 3.11 | `python:3.11-slim` | ~120 MB |
| Java 17 | `eclipse-temurin:17-jdk-jammy` | ~300 MB |
| C++ 17 | `python:3.11-slim` + `g++` | ~370 MB |

### 部署

- Docker Desktop / Docker Compose
- Nginx（生产环境反向代理）
- GitHub Actions（计划中）

## 前置要求

- **Docker Desktop**（含 Docker Compose）
- **Node.js 18+**
- **Python 3.11**（本地开发使用；容器部署可跳过）
- **Anaconda**（可选，用于 conda 环境）
- **Rust 1.75+**（仅桌面端开发需要）
- **Visual Studio Build Tools**（仅 Rust 编译需要，含 C++ 工作负载）

## 快速开始

### 方式一：完全容器化后端 + 本地前端开发（推荐）

**第一步：启动后端与数据库**

```bash
cd oj-platform
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

后端服务：http://localhost:8000
API 文档：http://localhost:8000/docs

**第二步：构建沙箱镜像**

```bash
cd backend
docker build -t judge-python:latest ./sandbox/python
docker build -t judge-java:latest ./sandbox/java
docker build -t judge-cpp:latest ./sandbox/cpp
```

**第三步：启动前端开发服务器**

```bash
cd frontend
npm install
npm run dev
```

前端页面：http://localhost:5173

**第四步：启动判题 worker（使用判题功能时需要）**

```bash
conda activate oj
cd backend
arq app.plugins.judge_plugin.worker.WorkerSettings
```

### 方式二：本地后端 + Docker 数据库

只需数据库和 Redis 用容器，后端在本地跑，便于调试：

```bash
# 只启动数据库和 Redis
docker compose up -d postgres redis

# 本地启动后端（新终端）
conda activate oj
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端（另一个终端）
cd frontend
npm run dev

# 启动 worker（另一个终端）
conda activate oj
cd backend
arq app.plugins.judge_plugin.worker.WorkerSettings
```

### 方式三：Tauri 桌面端

**前置**：

- Rust 工具链（`rustup`）
- Visual Studio Build Tools（含 C++ 工作负载）
- WebView2 Runtime（Win10/11 通常自带）

**启动**：

```bash
# 终端 1：前端 dev server
cd frontend
npm run dev

# 终端 2：Tauri dev（首次编译 Rust 3-10 分钟）
cd desktop
npm install
npm run tauri dev
```

**行为**：

- Tauri 启动时检查 `http://localhost:8000/health`
- 未响应 → 自动执行 `docker compose up -d`
- 等待后端就绪（最多 60 秒）
- 弹窗加载前端
- 系统托盘显示图标，右键菜单可用

### 方式四：前端预览打包产物

```bash
cd frontend
npm run build
npm run preview
```

预览地址：http://localhost:4173

## 管理员密钥

默认密钥：`admin-key-change-me`

修改方式：

```bash
cp .env.example .env
# 编辑 .env，修改 ADMIN_KEY 的值
docker compose restart backend
```

## 项目结构

```
oj-platform/
├── backend/
│   ├── app/
│   │   ├── core/                       # 核心基础设施
│   │   │   ├── config.py               # 配置类
│   │   │   ├── security.py             # 鉴权依赖
│   │   │   ├── password.py             # bcrypt 哈希
│   │   │   ├── jwt.py                  # JWT 工具
│   │   │   ├── event_bus.py            # Redis Pub/Sub
│   │   │   ├── events.py               # 事件名
│   │   │   ├── plugin_base.py          # Plugin 基类
│   │   │   ├── plugin_registry.py      # 插件注册表
│   │   │   ├── plugin_config_store.py  # 插件配置 DB
│   │   │   ├── task_queue.py           # arq 封装
│   │   │   └── ws_manager.py           # WS 连接管理
│   │   ├── models/                     # 9 张表
│   │   │   ├── category.py
│   │   │   ├── problem.py
│   │   │   ├── test_case.py
│   │   │   ├── research_subproject.py
│   │   │   ├── image.py
│   │   │   ├── plugin_config.py
│   │   │   ├── user.py
│   │   │   └── submission.py
│   │   ├── schemas/                    # Pydantic
│   │   ├── plugins/                    # 三个插件
│   │   │   ├── problem_plugin/
│   │   │   ├── user_plugin/
│   │   │   └── judge_plugin/
│   │   │       ├── __init__.py
│   │   │       ├── api.py
│   │   │       ├── service.py
│   │   │       ├── worker.py
│   │   │       ├── sandbox.py
│   │   │       ├── judge_python.py
│   │   │       ├── judge_java.py
│   │   │       └── judge_cpp.py
│   │   ├── database.py
│   │   └── main.py
│   ├── sandbox/                        # 沙箱镜像 Dockerfile
│   │   ├── python/
│   │   ├── java/
│   │   └── cpp/
│   ├── alembic/                        # 数据库迁移
│   ├── tests/                          # 测试（15 个文件）
│   ├── uploads/                        # 图片存储
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                        # API 封装
│   │   ├── components/                 # NavBar、CodeEditor、MarkdownRenderer
│   │   ├── router/                     # 路由 + 守卫
│   │   ├── stores/                     # Pinia
│   │   ├── styles/                     # Design Token
│   │   ├── utils/                      # axios、ws、tauri、marked
│   │   ├── views/                      # 9 个页面
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── desktop/                            # Tauri 桌面端
│   ├── package.json
│   └── src-tauri/
│       ├── Cargo.toml
│       ├── tauri.conf.json
│       ├── capabilities/
│       └── src/
│           ├── main.rs
│           ├── lib.rs
│           └── backend_launcher.rs
├── data/                               # 绑定挂载（不进版本库）
│   ├── postgres/
│   └── redis/
├── deploy/
│   └── nginx.conf
├── docs/
│   └── learning-log/                   # 学习笔记
├── docker-compose.yml
├── .env.example
└── README.md
```

## API 概览

### 公共接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查（含 redis） |
| GET | `/api/categories` | 分类列表 |
| GET | `/api/problems` | 题目列表（分页筛选） |
| GET | `/api/problems/{id}` | 题目详情 |
| GET | `/api/problems/{id}/answer` | 查看答案 |
| GET | `/api/tags` | 所有标签 |
| GET | `/api/images/{id}` | 访问图片 |

### 用户接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/users/me` | 当前用户 |
| PUT | `/api/users/me/password` | 修改密码 |
| GET | `/api/users/me/stats` | 个人统计 |

### 提交与判题

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/submissions` | 提交代码 |
| GET | `/api/submissions` | 我的提交列表 |
| GET | `/api/submissions/{id}` | 单条提交 |
| GET | `/api/problems/{id}/submissions` | 某题提交历史 |
| GET | `/api/widget/summary` | 桌面小组件摘要 |
| WS | `/api/submissions/{id}/ws?token=xxx` | 判题状态推送 |

### 管理员接口

**密钥方式**（`X-Admin-Key`）：

| 方法 | 路径 |
|---|---|
| POST | `/api/admin/problems` |
| PUT | `/api/admin/problems/{id}` |
| DELETE | `/api/admin/problems/{id}` |
| POST | `/api/admin/images` |
| GET | `/api/admin/plugins` |
| PUT | `/api/admin/plugins/{name}/enable` |
| PUT | `/api/admin/plugins/{name}/disable` |

**JWT 方式**（role=admin）：

| 方法 | 路径 |
|---|---|
| GET | `/api/admin/users` |
| PUT | `/api/admin/users/{id}/role` |
| PUT | `/api/admin/users/{id}/status` |
| GET | `/api/admin/stats` |

## 测试

```bash
cd backend
conda activate oj

# 非慢测试（约 1 分钟）
pytest tests/ -v --ignore=tests/test_judge_python.py --ignore=tests/test_judge_java.py --ignore=tests/test_judge_java_edge.py --ignore=tests/test_judge_cpp.py

# 全量测试（含沙箱，约 3 分钟）
pytest tests/ -v
```

**预期**：

- 非慢测试：73 passed
- 全量测试：94 passed

## 数据库迁移

```bash
cd backend

# 修改模型后生成迁移
alembic revision --autogenerate -m "描述"

# 人工审核生成的迁移文件（必做）
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

### 数据备份

```bash
# 数据库
docker exec oj-platform-postgres-1 pg_dump -U oj oj_platform > backup_$(date +%Y%m%d).sql

# 图片
xcopy backend\uploads uploads_backup /E /I /Y
```

### 生产环境（Nginx）

1. 打包前端

```bash
cd frontend
npm run build
```

2. 上传 `frontend/dist/` 到服务器 `/var/www/oj-platform/`

3. 使用 `deploy/nginx.conf`

```bash
sudo cp deploy/nginx.conf /etc/nginx/conf.d/oj-platform.conf
sudo nginx -t
sudo systemctl reload nginx
```

Nginx 配置包含：

- history 模式回退（`try_files $uri $uri/ /index.html`）
- `/api/` 转发到后端 8000
- **WebSocket 支持**（`proxy_set_header Upgrade $http_upgrade`）
- 静态资源缓存
- gzip 压缩

## 常见问题

### 容器内后端与本地 uvicorn 的选择

| 场景 | 后端运行方式 |
|---|---|
| 日常开发 | 本地 uvicorn --reload |
| 验证 Dockerfile | 容器 `docker compose up -d backend` |
| 生产部署 | 容器 + Nginx |

**注意**：容器内代码是构建时的快照。改源码后需重建：

```bash
docker compose up -d --build backend
```

### 图片 404 的常见原因

1. **数据库 file_path 格式不匹配**：本地 uvicorn 上传的图片路径是 Windows 绝对路径，容器内看不到。解决见 `image_api.py` 的 `get_image` 函数
2. **上传目录未挂载**：检查 `docker-compose.yml` 中 backend 服务的 volumes 配置
3. **Nginx 未转发 /api**：检查 `deploy/nginx.conf` 中的 `location /api/`

### WebSocket 连接失败

- 开发模式：`vite.config.ts` 的 `server.proxy` 需 `ws: true`
- 预览模式：`preview.proxy` 需 `ws: true`
- 生产环境：Nginx 需转发 `Upgrade` 和 `Connection` header

### 判题不生效

- **检查 worker 是否运行**：`arq app.plugins.judge_plugin.worker.WorkerSettings`
- **检查沙箱镜像**：`docker images | findstr judge-`
- **看 worker 日志**：终端输出
- **看数据库**：`SELECT id, status FROM submissions ORDER BY id DESC LIMIT 5;`

### 修改密钥未生效

```bash
docker compose restart backend
```

### Tauri 启动问题

- **编译慢**：首次编译 Rust 需 3-10 分钟，正常
- **`link.exe not found`**：装 Visual Studio Build Tools（含 C++ 工作负载）
- **WebView2 缺失**：下载安装 WebView2 Runtime
- **`cargo not found`**：重启终端让 PATH 生效

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
| style | 样式 |

### 数据库变更流程

1. 修改 `backend/app/models/` 下的模型
2. `alembic revision --autogenerate -m "描述"`
3. **人工审核生成的迁移脚本**（关键！`server_default` 位置、nullable 等）
4. `alembic upgrade head`
5. **立即备份**：`docker exec oj-platform-postgres-1 pg_dump -U oj oj_platform > backup.sql`
6. 提交迁移文件到 Git

### 代码风格

- **后端**：PEP 8，async/await，分层（路由 → 服务 → 模型）
- **前端**：Vue3 组合式 API，TypeScript，Design Token
- **数据库**：表名复数，外键 `xxx_id`，时间戳 `created_at`
- **Rust**：snake_case，`Result<T, E>` 错误处理

## 已知限制

- **Android 端未开始**：Capacitor 集成在 Day 21 计划中
- **Tauri 未打包**：`.msi` 安装包在 Day 22-23 计划中
- **图片本地存储**：多实例部署需共享存储
- **WS 单例跨进程**：0.2 单进程部署；多进程需 Redis Pub/Sub 广播
- **时区**：`created_at` 为 naive UTC，未按本地时区
- **JWT 无状态**：封禁用户后已发 token 仍有效
- **沙箱逃逸测试**：Fuzzing 测试在后续版本计划中

## 后续计划

### 0.2 剩余（Day 21-28）

- Android 原生小组件（Capacitor + Kotlin App Widget）
- Tauri 打包 `.msi` / `.deb` / `.AppImage`
- 前端打磨（骨架屏、错误提示、移动端适配）
- E2E 测试（Playwright）
- VitePress 文档站
- CI/CD（GitHub Actions）
- 0.2 版本发布

### 0.3 规划

- 数学题 OCR 扫描（PaddleOCR）
- AI 通用接口层（OpenAI / 通义千问）
- 离线优先数据同步
- 多端数据冲突合并

### 0.4+ 规划

- 桌面/移动小组件扩展
- 高并发与横向扩展
- K8s 部署方案
- 开源社区治理

## 贡献指南

欢迎任何形式的贡献：Issue、PR、文档改进、测试用例。

**推荐流程**：

1. Fork 仓库
2. 创建特性分支：`git checkout -b feature/xxx`
3. 提交改动：`git commit -m "feat: xxx"`
4. 推送：`git push origin feature/xxx`
5. 开启 Pull Request

**注意事项**：

- 遵循代码规范（见 `docs/learning-log/` 的提示词文档）
- 提交信息用 `feat:` / `fix:` 等前缀
- 新增功能补测试
- 保持中文注释/文档 UTF-8 编码

## 许可证

AGPLv3

本项目采用 GNU Affero 通用公共许可证第三版。任何修改后通过网络提供服务的行为，都需开源修改后的代码。

## 联系

见仓库 Issues 或 Discussions。

## 更新日志

### v0.2.0（进行中）

- 微内核架构重构
- 用户系统与 JWT 鉴权
- Python / Java / C++ 在线判题
- Docker 沙箱隔离
- WebSocket 实时推送
- Monaco Editor 集成
- Tauri 桌面端

### v0.1.0（已发布）

- 题库中心
- 5 种题型管理
- 图片上传
- Markdown 渲染与代码高亮
- Docker Compose 一键部署