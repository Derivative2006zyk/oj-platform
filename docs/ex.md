### 附：后端 0.1 版本进度

| 模块 | 状态 |
|---|---|
| 项目骨架 | 完成 |
| 数据库模型（5 张表） | 完成 |
| Alembic 迁移 + 预置分类 | 完成 |
| 分类/题目查询 API | 完成 |
| 题目 CRUD API | 完成 |
| 图片上传/访问 API | 完成 |
| 后端测试（11 个） | 完成 |
| 前端开发 | 待开始 |

### 附：常用排查命令

```
# Docker 相关
docker ps
docker logs oj-platform-postgres-1
docker exec -it oj-platform-postgres-1 psql -U oj -d oj_platform

# 数据库表操作
\dt
\d problems
SELECT * FROM categories;

# 后端相关
python -c "from app.main import app; [print(r.path) for r in app.routes]"
alembic current
alembic history
alembic upgrade head

# 测试相关
pytest tests/ -v
pytest tests/ -v -s
pytest tests/test_problems.py::test_get_categories -v
```

### 附：常见错误分类

#### 拼写错误
| 错误写法 | 正确写法 |
|---|---|
| DataTime | DateTime |
| dese() | desc() |
| inculde_router | include_router |
| content_typed | content_type |
| setting.UPLOAD_DIR | settings.UPLOAD_DIR |

#### 逻辑错误
| 错误 | 修复 |
|---|---|
| .scalar 少了括号 | .scalar() |
| 路由写成单数 | 改为复数 |
| 缺详情路由 | 补上 |
| 文件编码错误 | 改为 UTF-8 |

#### 环境错误
| 错误 | 原因 | 解决 |
|---|---|---|
| ConnectionRefusedError | 容器未启动 | docker compose up -d |
| Event loop is closed | 连接池跨 loop | 用 NullPool |
| ModuleNotFoundError | 工作目录不对 | cd backend |