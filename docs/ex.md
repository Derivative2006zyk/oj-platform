# 附录

### 一、项目 0.1 版本进度

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

### 二、常用排查命令

#### 1、Docker 相关

```
# 查看运行中的容器
docker ps

# 查看容器日志
docker compose logs backend
docker compose logs backend --tail 40
docker compose logs postgres

# 停止所有容器
docker compose down

# 停止并删除卷（数据丢失）
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
\d images

# 退出
\q
```

**单条 SQL 查询（不进入 psql）**：

```
docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT id, title FROM problems;"

docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT id, file_path FROM images ORDER BY id;"

docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform -c "SELECT * FROM categories ORDER BY sort_order;"
```

#### 3、后端相关

```
# 打印所有已注册路由
python -c "from app.main import app; [print(f'{sorted(r.methods)}  {r.path}') for r in app.routes]"

# Alembic 版本管理
alembic current
alembic history
alembic upgrade head
alembic downgrade -1

# 启动本地 uvicorn
conda activate oj
cd backend
uvicorn app.main:app --reload --port 8000
```

#### 4、前端相关

```
# 开发模式
cd frontend
npm run dev

# 打包
npm run build

# 预览打包产物
npm run preview

# 清空 Vite 缓存
rmdir /s /q node_modules\.vite
```

#### 5、测试相关

```
cd backend
conda activate oj

# 运行所有测试
pytest tests/ -v

# 显示 print 输出
pytest tests/ -v -s

# 运行单个测试
pytest tests/test_problems.py::test_get_categories -v

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

#### 3、环境错误

| 错误 | 原因 | 解决 |
|---|---|---|
| ConnectionRefusedError | 容器未启动 | `docker compose up -d` |
| Event loop is closed | 连接池跨 loop | 用 NullPool 或测试用 TESTING=1 |
| ModuleNotFoundError | 工作目录不对 | `cd backend` |
| async def functions not supported | 用了 base 环境 | `conda activate oj` |
| `href.startsWith is not a function` | marked renderer 新版签名 | 用字符串替换而非自定义 renderer |
| 图片文件已丢失 | file_path 格式不匹配 | 改造 get_image 兼容三种格式 |

#### 4、部署错误

| 错误 | 原因 | 解决 |
|---|---|---|
| 后端连不上 postgres | DATABASE_URL 用了 localhost | 改为服务名 `postgres` |
| 修改代码后容器未更新 | 容器是构建快照 | `build --no-cache` 或挂载源码 |
| 容器重启后数据丢失 | 卷未正确配置 | 检查 volumes 配置 |
| 端口被占用 | 其他进程占用 5432/8000 | `netstat -ano | findstr :8000` |
| Nginx history 模式刷新 404 | 未加 try_files | `try_files $uri $uri/ /index.html` |
| preview 模式 404 | 未配 `preview.proxy` | vite.config.ts 补上 |
| 打包后图片 404 | 相对路径 + 无代理 | 渲染时替换为后端绝对地址 |

### 四、关键调试技巧

#### 1、查看后端真实错误

```
docker compose logs backend --tail 50
```

**不要只看前端 F12 的错误信息**，一定要看后端日志。比如"图片文件已丢失"是后端主动抛的，日志里会记录完整路径。

#### 2、查看 F12 Network 的完整信息

- 点击请求 → Headers → 查看 **Request URL**（完整地址）
- 不要只看控制台的 `3:1` 之类行号
- 查看 **Status Code**、**Content-Type**
- 查看 **Response** 内容

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
python -c "from app.main import app; [print(f'{sorted(r.methods)}  {r.path}') for r in app.routes]"
```

判断某个路由是否注册、路径是单数还是复数。

### 五、日常开发流程速查

#### 1、本地开发模式（推荐日常使用）

```
# 终端 1：数据库
cd E:\github_project\oj-platform
docker compose up -d postgres

# 终端 2：后端（改动立即生效）
conda activate oj
cd E:\github_project\oj-platform\backend
uvicorn app.main:app --reload --port 8000

# 终端 3：前端
cd E:\github_project\oj-platform\frontend
npm run dev
```

访问 http://localhost:5173

#### 2、完全容器化模式

```
# 终端 1：后端 + 数据库
cd E:\github_project\oj-platform
docker compose up -d

# 终端 2：前端
cd E:\github_project\oj-platform\frontend
npm run dev
```

或预览打包产物：

```
npm run build
npm run preview
```

#### 3、验证打包产物

```
cd frontend
npm run build
npm run preview
```

访问 http://localhost:4173

### 六、Git 提交规范

| 类型 | 用途 |
|---|---|
| feat | 新增功能 |
| fix | 修复 bug |
| docs | 文档 |
| test | 测试代码 |
| refactor | 重构 |
| chore | 杂项 |

**推荐分批提交**，避免一次 `git add .`：

```
git add backend/
git commit -m "fix: 后端图片接口兼容多种 file_path 格式"

git add frontend/
git commit -m "fix: 前端图片渲染与 Vite 代理配置"

git add deploy/
git commit -m "docs: 添加 Nginx 部署配置"

git add docs/
git commit -m "docs: 添加第 12-13 天学习笔记"

git push origin main
```

### 七、版本发布流程

```
# 1. 确认工作区干净
git status

# 2. 推送到 main
git push origin main

# 3. 打标签
git tag -a v0.1.0 -m "Release 0.1.0: 题库中心"

# 4. 推送标签
git push origin v0.1.0

# 5. GitHub 上创建 Release
#    打开仓库 → Releases → Create a new release
#    选择 v0.1.0 标签，填写标题和描述
```

### 八、目录与文件速查

| 路径 | 用途 |
|---|---|
| `backend/app/core/config.py` | 配置类 |
| `backend/app/core/security.py` | 管理员鉴权 |
| `backend/app/models/` | 5 张表模型 |
| `backend/app/schemas/problem.py` | Pydantic 模型 |
| `backend/app/plugins/problem_plugin/api.py` | 题目 API 路由 |
| `backend/app/plugins/problem_plugin/service.py` | 业务逻辑 |
| `backend/app/plugins/problem_plugin/image_api.py` | 图片接口 |
| `backend/app/database.py` | 数据库引擎 |
| `backend/app/main.py` | FastAPI 入口 |
| `backend/alembic/env.py` | Alembic 环境配置 |
| `backend/tests/conftest.py` | 测试 fixtures |
| `backend/tests/test_problems.py` | 测试用例 |
| `backend/uploads/` | 图片存储 |
| `frontend/src/api/problem.ts` | API 封装 |
| `frontend/src/components/MarkdownRenderer.vue` | Markdown 渲染 |
| `frontend/src/utils/marked.ts` | marked 配置 |
| `frontend/src/router/index.ts` | 路由配置 |
| `frontend/src/views/ProblemList.vue` | 列表页 |
| `frontend/src/views/ProblemDetail.vue` | 详情页 |
| `frontend/src/views/ProblemEdit.vue` | 录入页 |
| `frontend/vite.config.ts` | Vite 配置（含代理） |
| `deploy/nginx.conf` | Nginx 配置示例 |
| `docker-compose.yml` | 容器编排 |
| `docs/learning-log/` | 学习笔记 |

### 九、端口占用速查

| 端口 | 服务 | 容器名 |
|---|---|---|
| 5173 | Vite dev server | 本地 |
| 4173 | Vite preview | 本地 |
| 8000 | FastAPI 后端 | oj-platform-backend-1 |
| 5432 | PostgreSQL | oj-platform-postgres-1 |

### 十、环境切换速查

| 提示符 | 环境 | 说明 |
|---|---|---|
| `(base)` | base 环境 | 缺少 pytest-asyncio 等，**不要用** |
| `(oj)` | oj 环境 | 项目专用，所有命令在此执行 |

每次打开新终端，先执行：

```
conda activate oj
```