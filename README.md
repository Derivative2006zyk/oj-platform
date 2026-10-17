# OJ Platform

多端互通模块化开源刷题系统

## 简介

一个面向数学与编程双场景的个人开源刷题工具，覆盖 Web、Windows、Linux，并支持通过局域网连接移动端。支持多题型题库管理、在线代码判题、实时状态推送。

后端采用 FastAPI + PostgreSQL + Redis 微内核架构，所有业务功能组织为可热插拔插件。前端 Vue3 + Vite + TypeScript，桌面端使用 Tauri 打包，内置 Docker 引擎自动拉起机制，实现一键开箱即用。

## 当前版本

- **0.1.0**（已发布）：题库中心，5 种题型管理 + 图片 + Markdown
- **0.2.0**（开发完成）：微内核 + 用户系统 + 三语言判题 + WebSocket + 桌面端打包 + 题库导入导出

## 核心特性

- **多端互通**：支持 Windows 桌面端、Web 端，并通过局域网与移动端数据互通。
- **安全沙箱判题**：基于 Docker 隔离的本地判题系统，支持 Python、Java、C++ 多语言安全运行。
- **多种题型**：支持算法题、选择题、填空题、证明题、科研项目等多种题型。
- **题库导入导出**：一键打包题库为 ZIP，支持分类与题库折叠筛选，支持一键导入恢复。
- **极简部署**：无需手动配置 Python/Node 环境，桌面端双击安装，内置启动器自动调度 Docker 引擎拉起底层服务。

---

## 面向终端用户：安装与使用

### 系统要求

- **操作系统**：Windows 10/11 (x64)
- **运行环境**：必须安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **浏览器核心**：WebView2 Runtime（Windows 11 已内置，Windows 10 可能需要单独安装）

### 快速安装步骤

1. 安装并启动 Docker Desktop。安装时请勾选 "Use WSL 2 instead of Hyper-V"。确保任务栏右下角小鲸鱼图标变绿。
2. 双击 `OJ Platform_0.2.0_x64_en-US.msi` 按向导安装。
3. 从开始菜单或桌面启动 OJ Platform。
4. 首次启动会自动在后台初始化数据库、拉取基础镜像并启动判题服务，预计需要 1-2 分钟。请耐心等待主窗口出现。

### 国内网络配置（必看）

由于首次启动需要从 Docker Hub 拉取基础镜像，国内直连极可能超时。请提前配置镜像加速器：

1. 打开 Docker Desktop，点击右上角设置（齿轮图标） -> Docker Engine。
2. 在 JSON 配置中添加 `registry-mirrors`：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me",
    "https://docker.m.daocloud.io"
  ]
}
```

3. 点击 Apply & Restart，等待 Docker 重启完成。

### 移动端连接（局域网）

若需在手机或平板上使用，请确保设备与电脑连接同一个 WiFi。
1. 在桌面端进入设置页面。
2. 查看页面上显示的本机后端地址（如 `http://192.168.1.100:8000`）。
3. 在移动端 App 的设置中填入该地址。

---

## 数据位置与高危操作

所有数据（题库、账号、判题记录、图片）均保存在系统的用户目录中。卸载或更新软件不会导致数据丢失。

- **Windows**: `%APPDATA%\oj-platform\`
- **macOS**: `~/Library/Application Support/oj-platform/`
- **Linux**: `~/.local/share/oj-platform/`

### 高危操作：彻底重置软件（清空所有数据）

**【警告】平时更新软件、卸载重装或重启 Docker 都不需要执行此操作。**
只有在遇到数据库严重损坏，或者你想把软件彻底恢复成全新纯净状态时，才需要使用以下命令。此操作会永久删除所有题库、账号及提交记录，且无法恢复。执行前请务必完全退出 OJ Platform 软件。

请根据你使用的终端，选择对应的命令执行：

- CMD（命令提示符）:
  ```cmd
  rmdir /s /q %APPDATA%\oj-platform
  ```

- PowerShell:
  ```powershell
  Remove-Item -Path "$env:APPDATA\oj-platform" -Recurse -Force
  ```

- Git Bash / WSL:
  ```bash
  rm -rf "$APPDATA/oj-platform"
  ```

- macOS / Linux 终端:
  ```bash
  # macOS
  rm -rf ~/Library/Application\ Support/oj-platform
  # Linux
  rm -rf ~/.local/share/oj-platform
  ```

执行完毕后，重新启动 OJ Platform。软件会自动解压最新配置并初始化一个全新的空数据库。

---

## 面向开发者：源码部署与调试

### 前置要求

- Docker Desktop（含 Docker Compose）
- Node.js 18+
- Python 3.11（本地调试后端时使用）
- Rust 1.75+ 及 Visual Studio Build Tools（仅桌面端 Tauri 开发需要）

### 方式一：全容器化后端 + 本地前端开发（推荐）

第一步：启动后端基础设施与自动构建判题镜像
```bash
cd oj-platform
docker compose up -d --build
```
此命令会自动启动 PostgreSQL、Redis、Backend、Worker，并利用沙箱 Dockerfile 构建判题镜像。

第二步：启动前端开发服务器
```bash
cd frontend
npm install
npm run dev
```
前端页面访问：http://localhost:5173

### 方式二：Tauri 桌面端开发

前置：确保 Rust 工具链配置正确。

```bash
# 终端 1：前端 dev server
cd frontend
npm run dev

# 终端 2：Tauri dev（首次编译 Rust 需要几分钟）
cd desktop
npm install
npm run tauri dev
```

### 方式三：构建桌面端安装包

```bash
cd desktop
npm run tauri build
```
生成的安装包位于 `desktop/src-tauri/target/release/bundle/` 目录下。

---

## 技术栈概览

### 后端

| 组件 | 版本 | 用途 |
|---|---|---|
| FastAPI | 0.115+ | Web 框架 |
| Uvicorn | 0.30+ | ASGI 服务器 |
| SQLAlchemy | 2.0 (async) | ORM |
| asyncpg | 0.31+ | PostgreSQL 异步驱动 |
| Alembic | 1.13+ | 数据库迁移 |
| Pydantic | 2.x | 数据校验 |
| Redis | 7.x | 事件总线、缓存、队列 |
| arq | 0.26+ | 异步任务队列 |
| python-jose | 3.3.0 | JWT |
| passlib + bcrypt | - | 密码哈希 |
| Pillow | 10.x | 图片校验 |
| Pytest | 8.x | 测试框架 |

### 前端与桌面端

| 组件 | 版本 | 用途 |
|---|---|---|
| Vue | 3.5+ | 前端框架 |
| Vite | 5.x+ | 构建工具 |
| TypeScript | 5.x+ | 类型系统 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由 |
| Axios | 1.x | HTTP 客户端 |
| Monaco Editor | 0.52.2 | 代码编辑器 |
| Marked | 12.x+ | Markdown 渲染 |
| Tauri | 2.x | 桌面壳 |
| Rust | 1.75+ | 原生逻辑与启动器 |

---

## API 概览

### 公共接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查（含 redis） |
| GET | `/api/categories` | 分类列表 |
| GET | `/api/problems` | 题目列表（分页筛选） |
| GET | `/api/problems/{id}` | 题目详情 |
| GET | `/api/tags` | 所有标签 |
| GET | `/api/images/{id}` | 访问图片 |

### 用户与提交接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/users/me` | 当前用户 |
| POST | `/api/submissions` | 提交代码 |
| GET | `/api/submissions` | 我的提交列表 |
| WS | `/api/submissions/{id}/ws` | 判题状态推送 |

### 管理员接口

密钥方式（Header: `X-Admin-Key`）或 JWT 方式（role=admin）。

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/admin/problems` | 创建题目 |
| POST | `/api/admin/bank/export` | 导出题库 |
| POST | `/api/admin/bank/import` | 导入题库 |
| GET | `/api/admin/users` | 用户列表（JWT） |
| GET | `/api/admin/stats` | 全局统计（JWT） |

---

## 常见问题与排查

### 提示无法启动后端服务，后台服务未启动

请检查任务栏右下角是否打开了 Docker Desktop。如果没有，请从开始菜单启动，等待小鲸鱼图标由橙色变为绿色后，重新打开本软件。

### 报错无法访问 Docker Hub 拉取镜像

请参考上文【国内网络配置】章节，配置镜像加速器。若依然超时，请尝试关闭 IPv6 或配置代理。

### 提交代码后一直显示排队中

说明判题队列（Worker）未能成功消费任务。
1. 检查 Docker 面板中 `oj-platform-worker-1` 容器是否处于运行状态（Up）。
2. 若 Worker 未启动，退出软件并重启，或打开终端在项目目录执行 `docker compose up -d`。

### 修改管理员密钥未生效

修改 `.env` 文件后，需要重启后端容器：
```bash
docker compose restart backend
```

---

## 更新日志

### v0.2.0（当前版本）

- 微内核架构重构与用户系统
- Python / Java / C++ 在线判题与 Docker 安全隔离
- WebSocket 实时状态推送与 Monaco Editor 集成
- 题库导入导出与题库分类折叠
- Tauri 桌面端支持，内置自动拉起引擎与镜像加速引导

### v0.1.0

- 题库中心、多题型管理、Markdown 渲染

## 许可证

AGPLv3
本项目采用 GNU Affero 通用公共许可证第三版。任何修改后通过网络提供服务的行为，都需开源修改后的代码。