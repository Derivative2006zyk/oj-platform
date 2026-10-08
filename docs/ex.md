# 附录

### 一、项目版本进度

#### 0.1 版本（题库中心，已发布）

| 模块 | 状态 |
|---|---|
| 项目骨架 | 完成 |
| 数据库模型（5 张表） | 完成 |
| Alembic 迁移 + 预置分类 | 完成 |
| 分类/题目查询 API | 完成 |
| 题目 CRUD API | 完成 |
| 图片上传/访问 API | 完成 |
| 后端测试（11 个） | 完成 |
| 前端初始化与路由 | 完成 |
| 题目列表页 | 完成 |
| 题目详情页 | 完成 |
| 题目录入页（上） | 完成 |
| 题目录入页（下）与联调 | 完成 |
| Docker 部署与文档 | 完成 |
| 最终验收与发布（v0.1.0） | 完成 |

#### 0.2 版本（判题与桌面端，进行中）

| 天 | 模块 | 状态 |
|---|---|---|
| Day 1 | Redis 接入 + 事件总线基座 | 完成 |
| Day 2 | 插件注册表 + `@register_plugin` | 完成 |
| Day 3 | 插件配置持久化 + 事件发布 | 完成 |
| Day 4 | 用户系统（模型 + JWT + 鉴权） | 完成 |
| Day 5 | 前端登录注册 + 路由守卫 | 完成 |
| Day 6 | Submission 模型 + 提交 API + arq 队列 | 完成 |
| Day 7 | Python 沙箱镜像与判题 | 完成 |
| Day 8 | Java 沙箱镜像与判题 | 完成 |
| Day 9 | C++ 沙箱镜像与判题 | 完成 |
| Day 10 | WebSocket 实时推送判题状态 | 完成 |
| Day 11 | 提交历史页 + 个人中心 | 完成 |
| Day 12 | Monaco Editor 集成 | 完成 |
| Day 13 | Java 沙箱 JVM 限制 + 编译缓存 | 完成 |
| Day 14 | 题目详情页提交历史区块 | 完成 |
| Day 15 | 后端用户系统完善（管理员） | 完成 |
| Day 16 | 前端管理员页面 | 完成 |
| Day 17 | Tauri 桌面端初始化 | 完成 |
| Day 18 | Tauri 自动拉起本地后端 | 完成 |
| Day 19 | Tauri 系统托盘 | 完成 |
| Day 20 | 桌面小组件数据接口 + 托盘 tooltip | 完成 |
| Day 21 | Android 原生小组件 | 未开始 |
| Day 22 | Tauri 打包 .msi | 未开始 |
| Day 23 | Tauri 资源打包 | 未开始 |
| Day 24 | 前端打磨 | 未开始 |
| Day 25 | E2E 测试（Playwright） | 未开始 |
| Day 26 | 文档与部署脚本 | 未开始 |
| Day 27 | CI/CD | 未开始 |
| Day 28 | 0.2 版本发布 + tag v0.2.0 | 未开始 |

### 二、常用排查命令

#### 1、Docker 相关

```
# 查看运行中的容器
docker ps
docker compose ps

# 查看容器日志
docker compose logs backend
docker compose logs backend --tail 40
docker compose logs postgres
docker compose logs redis

# 停止所有容器
docker compose down

# 停止并删除卷（数据丢失，迁移期间禁用）
docker compose down -v

# 重建后端镜像（不用缓存）
docker compose build --no-cache backend
docker compose up -d backend

# 重启某个服务
docker compose restart backend
```

#### 2、数据库操作

```
# 进入 psql
docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform

# 列出所有表
\dt

# 查看表结构
\d problems
\d users
\d submissions
\d plugin_configs

# 退出
\q
```

**单条 SQL 查询（不进入 psql）**：

```
docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT id, title FROM problems;"

docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT id, username, role, is_active FROM users;"

docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT id, language, status FROM submissions ORDER BY id DESC LIMIT 5;"

docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT * FROM plugin_configs;"
```

**备份与恢复**：

```
# 备份
docker exec oj-platform-postgres-1 pg_dump -U oj oj_platform > backup.sql

# 恢复
type backup.sql | docker exec -i oj-platform-postgres-1 psql -U oj -d oj_platform
```

#### 3、后端相关

```
# 打印所有已注册路由
python -c "from app.main import app; [print(f'{sorted(r.methods)}  {r.path}') for r in app.routes if hasattr(r, 'methods')]"

# Alembic 版本管理
alembic current
alembic history
alembic upgrade head
alembic downgrade -1

# 启动本地 uvicorn
conda activate oj
cd backend
uvicorn app.main:app --reload --port 8000

# 启动 arq worker
arq app.plugins.judge_plugin.worker.WorkerSettings
```

#### 4、沙箱镜像构建

```
cd backend

# Python 沙箱
docker build -t judge-python:latest ./sandbox/python

# Java 沙箱（用 eclipse-temurin 替代 openjdk:17-slim）
docker build -t judge-java:latest ./sandbox/java

# C++ 沙箱（用 python:3.11-slim + apt 装 g++）
docker build -t judge-cpp:latest ./sandbox/cpp

# 查看已构建的沙箱镜像
docker images | findstr judge-
```

#### 5、前端相关

```
cd frontend

# 开发模式
npm run dev

# 打包
npm run build

# 预览打包产物
npm run preview

# 清空 Vite 缓存
rmdir /s /q node_modules\.vite
```

#### 6、Tauri 桌面端

```
cd desktop

# 安装依赖
npm install

# 开发模式（会编译 Rust）
npm run tauri dev

# 打包
npm run tauri build

# 清 Rust 缓存
cd src-tauri
cargo clean
```

#### 7、测试相关

```
cd backend
conda activate oj

# 运行所有测试（含沙箱慢测试，约 3 分钟）
pytest tests/ -v

# 只跑非慢测试（约 1 分钟）
pytest tests/ -v --ignore=tests/test_judge_python.py --ignore=tests/test_judge_java.py --ignore=tests/test_judge_java_edge.py --ignore=tests/test_judge_cpp.py

# 显示 print 输出
pytest tests/ -v -s

# 运行单个测试
pytest tests/test_user.py::test_register_success -v

# 遇到失败立即停止
pytest tests/ -x
```

### 三、常见错误分类

#### 1、拼写错误

| 错误写法 | 正确写法 |
|---|---|
| DataTime | DateTime |
| dese() | desc() |
| inculde_router | include_router |
| content_typed | content_type |
| setting.UPLOAD_DIR | settings.UPLOAD_DIR |

#### 2、逻辑错误

| 错误 | 修复 |
|---|---|
| .scalar 少了括号 | .scalar() |
| 路由写成单数 | 改为复数 |
| 缺详情路由 | 补上 `/problems/{id}` |
| 路由路径缺少开头 `/` | path 必须以 `/` 开头 |
| 文件编码错误 | 改为 UTF-8 |
| `marked.use` 写在组件内 | 移到模块顶层 |
| 选项 key 不重排 | 删除后 forEach 重新分配 |
| `runtime_ms !== null` 判 undefined | 改 `!= null` |

#### 3、环境错误

| 错误 | 原因 | 解决 |
|---|---|---|
| ConnectionRefusedError | 容器未启动 | `docker compose up -d` |
| Event loop is closed | 连接池跨 loop | 用 NullPool 或 TESTING=1 |
| ModuleNotFoundError | 工作目录不对 | `cd backend` |
| async def functions not supported | 用了 base 环境 | `conda activate oj` |
| `href.startsWith is not a function` | marked renderer 新版签名 | 用字符串替换而非自定义 renderer |
| 图片文件已丢失 | file_path 格式不匹配 | 改造 get_image 兼容三种格式 |
| `can't subtract offset-naive and offset-aware datetimes` | aware/naive 混用 | `datetime.now(timezone.utc).replace(tzinfo=None, ...)` |
| `another operation is in progress` | 连接池跨 loop | `TESTING=1` 时用 NullPool |

#### 4、部署错误

| 错误 | 原因 | 解决 |
|---|---|---|
| 后端连不上 postgres | DATABASE_URL 用了 localhost | 改为服务名 `postgres` |
| 修改代码后容器未更新 | 容器是构建快照 | `build --no-cache` 或挂载源码 |
| 容器重启后数据丢失 | 卷未正确配置 | 检查 volumes 配置 |
| 端口被占用 | 其他进程占用 5432/8000 | `netstat -ano \| findstr :8000` |
| Nginx history 模式刷新 404 | 未加 try_files | `try_files $uri $uri/ /index.html` |
| preview 模式 404 | 未配 `preview.proxy` | vite.config.ts 补上 |
| 打包后图片 404 | 相对路径 + 无代理 | 渲染时替换为后端绝对地址 |
| WS 握手失败 | Vite 未开 `ws: true` | server.proxy 和 preview.proxy 都加 |
| 迁移文件生成但未执行 | 忘记 upgrade | `alembic upgrade head` |
| 库表丢失但 alembic 记录最新 | 版本与数据脱节 | 清 schema 后 `alembic upgrade head` |

#### 5、0.2 新增坑

| 错误 | 原因 | 解决 |
|---|---|---|
| `AttributeError: module 'bcrypt' has no attribute '__about__'` | bcrypt 版本太新 | 锁 `bcrypt==4.0.1` |
| `EmailStr` 导入失败 | 缺 email-validator | `pip install email-validator` |
| `/api/auth/*` 404 | `user_plugin/init.py` 少双下划线 | 改名 `__init__.py` |
| `@register_plugin` 未执行 | 同上 | 检查文件名和装饰器 |
| `py_compile` 报 CE | `--read-only` 下写 `.pyc` 失败 | 用 `ast.parse` |
| Java 每测试点重编译 | 未优化 | 拆 compile + run，tmpdir 复用 |
| JVM OOM 误判 MLE | `-Xmx` 未限制 | 加 JVM 参数 |
| `gcc:13-slim` 403 | 网络限制 | 用 `python:3.11-slim + apt` |
| `openjdk:17-slim` 403 | 网络限制 | 用 `eclipse-temurin:17-jdk-jammy` |
| `tauri_plugin_opener` 缺失 | 模板引用未装插件 | lib.rs 改用 dialog |
| 托盘 tooltip 不显示 | 前端未调 IPC | 前端 `refreshTrayFromBackend` |
| 最小化后托盘无响应 | `is_visible()` 仍为 true | 加 `is_minimized()` 判断 |
| 菜单跳转 pushState 无效 | Vue Router 不响应 | 用 `location.href` |
| 托盘 `tray_by_id` 找不到 | 未 with_id | `TrayIconBuilder::with_id("main")` |

### 四、关键调试技巧

#### 1、查看后端真实错误

```
docker compose logs backend --tail 50
```

**不要只看前端 F12 的错误信息**，一定要看后端日志。比如"图片文件已丢失"是后端主动抛的，日志里会记录完整路径。

#### 2、查看 F12 Network 的完整信息

- 点击请求 → Headers → 查看 **Request URL**（完整地址）
- 查看 **Status Code**、**Content-Type**、**Response**

#### 3、查看容器内文件

```
docker exec -it oj-platform-backend-1 ls /app/uploads/2026/09
docker exec -it oj-platform-backend-1 cat /app/app/plugins/problem_plugin/image_api.py
```

对照宿主机文件，判断容器内代码是不是最新版。

#### 4、查看数据库真实内容

```
docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT id, description FROM problems WHERE id = 5;"
```

有时前端显示乱码、404，其实是数据库里存的数据格式问题。

#### 5、打印所有路由

```
cd backend
python -c "from app.main import app; [print(f'{sorted(r.methods)}  {r.path}') for r in app.routes if hasattr(r, 'methods')]"
```

判断某个路由是否注册、路径是单数还是复数。

#### 6、查看 Redis 事件总线状态

```
docker exec -it oj-platform-redis-1 redis-cli

# 内
PING                     # 应返回 PONG
SUBSCRIBE oj:events      # 实时看事件
PUBLISH test.channel "hi"   # 手动发布
```

#### 7、查看 arq 队列

```
docker exec -it oj-platform-redis-1 redis-cli

# 内
KEYS arq:*
LLEN arq:queue:default
```

### 五、日常开发流程速查

#### 1、完整开发模式（推荐）

```
# 终端 1：数据库 + Redis
cd E:\github_project\oj-platform
docker compose up -d postgres redis

# 终端 2：后端（改动立即生效）
conda activate oj
cd E:\github_project\oj-platform\backend
uvicorn app.main:app --reload --port 8000

# 终端 3：前端
cd E:\github_project\oj-platform\frontend
npm run dev

# 终端 4：worker（判题时启动）
conda activate oj
cd E:\github_project\oj-platform\backend
arq app.plugins.judge_plugin.worker.WorkerSettings
```

访问 http://localhost:5173

#### 2、完全容器化模式

```
# 终端 1：后端 + 数据库 + Redis
cd E:\github_project\oj-platform
docker compose up -d

# 终端 2：前端
cd E:\github_project\oj-platform\frontend
npm run dev
```

#### 3、Tauri 桌面端模式

```
# 终端 1：前端 dev（Tauri 加载 5173）
cd E:\github_project\oj-platform\frontend
npm run dev

# 终端 2：Tauri dev（会编译 Rust，首次慢）
cd E:\github_project\oj-platform\desktop
npm run tauri dev
```

**若后端未启动**，Tauri 会自动执行 `docker compose up -d`。

### 六、Git 提交规范

| 类型 | 用途 |
|---|---|
| feat | 新增功能 |
| fix | 修复 bug |
| docs | 文档 |
| test | 测试代码 |
| refactor | 重构 |
| chore | 杂项 |
| style | 样式 |

**推荐分批提交**，避免 `git add .`：

```
git add backend/
git commit -m "feat: 用户注册/登录成功后发布事件"

git add frontend/
git commit -m "feat: 题目详情页加提交面板与实时状态"

git add docs/
git commit -m "docs: 添加第 28 天学习笔记"

git push origin main
```

### 七、版本发布流程

```
# 1. 确认工作区干净
git status

# 2. 推送到 main
git push origin main

# 3. 打标签
git tag -a v0.2.0 -m "Release 0.2.0: 判题与桌面端"

# 4. 推送标签
git push origin v0.2.0

# 5. GitHub 上创建 Release
```

### 八、目录与文件速查（0.2 完成后的实际结构）

| 路径 | 用途 |
|---|---|
| `backend/app/core/config.py` | 配置类 |
| `backend/app/core/security.py` | 鉴权依赖（admin key + JWT） |
| `backend/app/core/password.py` | bcrypt 密码哈希 |
| `backend/app/core/jwt.py` | JWT 工具 |
| `backend/app/core/event_bus.py` | Redis Pub/Sub 事件总线 |
| `backend/app/core/events.py` | 事件名常量 |
| `backend/app/core/plugin_base.py` | Plugin 抽象基类 |
| `backend/app/core/plugin_registry.py` | PluginRegistry + `@register_plugin` |
| `backend/app/core/plugin_config_store.py` | plugin_configs 读写 |
| `backend/app/core/task_queue.py` | arq 投递封装 |
| `backend/app/core/ws_manager.py` | WebSocket 连接管理 |
| `backend/app/models/` | 9 张表模型 |
| `backend/app/schemas/` | Pydantic 模型 |
| `backend/app/plugins/problem_plugin/` | 题库插件 |
| `backend/app/plugins/user_plugin/` | 用户插件 |
| `backend/app/plugins/judge_plugin/` | 判题插件 |
| `backend/app/database.py` | 数据库引擎（含 NullPool 逻辑） |
| `backend/app/main.py` | FastAPI 入口（lifespan + 插件注册） |
| `backend/sandbox/python/Dockerfile` | Python 沙箱 |
| `backend/sandbox/java/Dockerfile` | Java 沙箱 |
| `backend/sandbox/cpp/Dockerfile` | C++ 沙箱 |
| `backend/alembic/env.py` | Alembic 环境配置 |
| `backend/tests/conftest.py` | 测试 fixtures |
| `frontend/src/api/` | API 封装（problem、auth、user、admin、submission） |
| `frontend/src/stores/user.ts` | Pinia 用户状态 |
| `frontend/src/utils/axios.ts` | 统一 axios + 拦截器 |
| `frontend/src/utils/ws.ts` | WebSocket 客户端 |
| `frontend/src/utils/tauri.ts` | Tauri 环境检测与 IPC |
| `frontend/src/utils/marked.ts` | marked 配置 |
| `frontend/src/styles/tokens.css` | Design Token |
| `frontend/src/views/` | 9 个页面 |
| `frontend/src/components/` | NavBar、CodeEditor、MarkdownRenderer |
| `frontend/vite.config.ts` | Vite 配置（含 WS 代理） |
| `desktop/src-tauri/src/main.rs` | Tauri 主入口（托盘 + IPC） |
| `desktop/src-tauri/src/backend_launcher.rs` | 自动拉起后端 |
| `desktop/src-tauri/src/lib.rs` | Tauri lib 入口 |
| `desktop/src-tauri/tauri.conf.json` | Tauri 配置 |
| `desktop/src-tauri/capabilities/default.json` | Tauri 权限 |
| `deploy/nginx.conf` | Nginx 配置示例 |
| `docker-compose.yml` | 容器编排（postgres + redis + backend） |
| `data/` | 绑定挂载数据目录（不进版本库） |
| `docs/learning-log/` | 学习笔记 |

### 九、端口占用速查

| 端口 | 服务 | 容器名 |
|---|---|---|
| 5173 | Vite dev server | 本地 |
| 4173 | Vite preview | 本地 |
| 8000 | FastAPI 后端 | oj-platform-backend-1 |
| 5432 | PostgreSQL | oj-platform-postgres-1 |
| 6379 | Redis | oj-platform-redis-1 |

### 十、环境切换速查

| 提示符 | 环境 | 说明 |
|---|---|---|
| `(base)` | base 环境 | 缺少 pytest-asyncio 等，**不要用** |
| `(oj)` | oj 环境 | 项目专用，所有命令在此执行 |

每次打开新终端，先执行：

```
conda activate oj
```

### 十一、数据卷与迁移

**0.2 起，数据卷使用绑定挂载**：

```
data/
├── postgres/          # PostgreSQL 数据文件
└── redis/             # Redis AOF 文件
```

**备份**：

```
docker exec oj-platform-postgres-1 pg_dump -U oj oj_platform > backup_$(date +%Y%m%d).sql
```

**恢复**：

```
type backup_xxx.sql | docker exec -i oj-platform-postgres-1 psql -U oj -d oj_platform
```

**迁移步骤**（从旧版本升级）：

1. 备份
2. `docker compose down`（不加 `-v`）
3. 修改 `docker-compose.yml`
4. `docker compose up -d`
5. 恢复数据
6. 迁移完成

### 十二、Tauri 桌面端使用

**首次启动**：

1. 确保 Docker Desktop 运行
2. 双击桌面端图标
3. Tauri 检查后端 → 未启动则自动执行 `docker compose up -d`
4. 等待 10-30 秒
5. 窗口弹出

**系统托盘**：

- 左键：显示/隐藏窗口
- 右键菜单：显示窗口、隐藏窗口、提交历史、统计、退出
- 悬停：显示刷题统计（需前端已登录）

**关闭窗口**：

- 点右上角 X → 窗口隐藏到托盘（不退出）
- 要真正退出 → 托盘右键 → 退出

**项目路径**：

- Tauri 默认从 `E:\github_project\oj-platform` 启动后端
- 可通过环境变量 `OJ_PROJECT_ROOT` 覆盖