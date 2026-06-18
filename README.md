# KouOJ

KouOJ 是一个基于 Django、MySQL 和 Vue 3 的前后端分离在线判题系统，适用于数据库课程设计、Python 课程设计和项目实训。

系统已经实现从题目管理、在线编码、代码提交、自动判题到提交分析的完整流程，并提供前端管理员工作台、个人刷题统计、题解、公告、AI 错误分析和操作日志。

## 功能概览

### 普通用户

- 注册、登录、退出和 JWT 身份认证
- 浏览、搜索和筛选题目
- 查看题目详情和公开样例
- 使用 CodeMirror 在线编写 Python、C 和 C++ 代码
- 提交代码并查看实时判题状态
- 按状态筛选提交记录，查看测试点详情
- 发布、编辑和删除自己的题解
- 修改个人资料和密码
- 查看 AC 数量、难度统计和刷题热力图
- 使用 AI 助手分析错误提交

### 管理员

- 使用 Vue 管理工作台维护题目、标签、测试点和公告
- 创建、编辑、删除题目并设置难度、限制、标签和公开状态
- 管理公开样例和隐藏测试点
- 控制公告发布和置顶状态
- 查看全部提交记录
- 使用 Django Admin 管理用户和查看操作日志

### 判题系统

- Python 3、C11 和 C++17
- 独立 Judge Worker
- Python `subprocess` 执行
- C/C++ 使用 `gcc:13` Docker 容器编译和运行
- 支持 AC、WA、TLE、RE、CE 和系统错误
- 保存每个测试点的输出、耗时和错误信息
- 使用事务和行锁避免多个 Worker 重复获取同一提交

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite |
| UI | Element Plus、CodeMirror 6 |
| 状态与路由 | Pinia、Vue Router |
| HTTP | Axios |
| 后端 | Python、Django 4.2、Django REST Framework |
| 数据库 | MySQL |
| 认证 | SimpleJWT |
| 筛选 | django-filter |
| 判题 | subprocess、Docker、GCC 13 |
| AI | LangGraph、Tavily、OpenAI-compatible API |

## 系统架构

```text
Vue 3 前端
  ├─ 普通用户页面
  ├─ 管理员工作台
  └─ Axios + JWT
          │
          ▼
Django REST Framework
  ├─ accounts       用户与个人统计
  ├─ problems       题目、标签与测试点
  ├─ submissions    提交与判题结果
  ├─ judge          判题服务
  ├─ solutions      题解
  ├─ announcements  公告
  ├─ home           首页聚合接口
  ├─ ai_agent       AI 提交分析
  └─ audit          操作日志
          │
          ├──────────────► MySQL
          │
          └──────────────► Judge Worker
                              ├─ Python subprocess
                              └─ Docker gcc:13
```

## 项目结构

```text
KouOJ/
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── ai_agent/
│   │   ├── announcements/
│   │   ├── audit/
│   │   ├── home/
│   │   ├── judge/
│   │   ├── problems/
│   │   ├── solutions/
│   │   └── submissions/
│   ├── config/
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── types/
│   │   ├── utils/
│   │   └── views/
│   └── package.json
├── docs/
├── .env.example
└── requirements.txt
```

## 环境要求

- Python 3.10 或兼容版本
- Node.js 和 npm
- MySQL 8.x
- Docker Desktop，用于 C/C++ 判题

Windows 和 WSL 不要共用同一个 Python 虚拟环境。

## 本地运行

### 1. 创建 Python 虚拟环境

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果 PowerShell 禁止执行激活脚本，可以直接使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 创建 MySQL 数据库

```sql
CREATE DATABASE kouoj
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

建议创建独立数据库用户，不要在生产环境使用 MySQL `root`。

### 3. 配置环境变量

将 `.env.example` 复制为 `.env`，至少填写数据库配置：

```text
KOUOJ_SECRET_KEY=请替换为自己的密钥
KOUOJ_DEBUG=1
KOUOJ_ALLOWED_HOSTS=127.0.0.1,localhost

KOUOJ_DB_NAME=kouoj
KOUOJ_DB_USER=root
KOUOJ_DB_PASSWORD=你的MySQL密码
KOUOJ_DB_HOST=localhost
KOUOJ_DB_PORT=3306
```

`.env` 包含密码和 API Key，不要提交到 Git。

AI 功能为可选功能。需要启用时继续配置：

```text
KOUOJ_TAVILY_API_KEY=
KOUOJ_AI_MODEL_BASE_URL=
KOUOJ_AI_MODEL_API_KEY=
KOUOJ_AI_MODEL_NAME=
```

未配置外部服务时，基础 OJ 功能仍可使用，AI 模块会跳过搜索或返回降级提示。

### 4. 初始化数据库

```powershell
cd backend
python manage.py migrate
python manage.py createsuperuser
```

通常只在修改 Django Model 后才需要运行：

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 5. 启动 Django

```powershell
cd backend
python manage.py runserver
```

- API：`http://127.0.0.1:8000/api/`
- Django Admin：`http://127.0.0.1:8000/admin/`

### 6. 启动判题 Worker

另开一个终端，进入相同虚拟环境：

```powershell
cd backend
python manage.py run_judge
```

只处理一个待判题任务：

```powershell
python manage.py run_judge --once
```

### 7. 准备 C/C++ 判题镜像

确保 Docker Desktop 已启动：

```powershell
docker pull gcc:13
docker image ls
```

### 8. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173/`

生产构建：

```powershell
npm run build
```

## 创建管理员

公开注册接口只创建普通用户，不允许用户自行注册管理员。

### 创建超级管理员

```powershell
cd backend
python manage.py createsuperuser
```

超级管理员的 `is_staff=True`，系统会将其识别为管理员。重新登录前端后，导航栏会显示“管理”入口：

```text
http://localhost:5173/admin
```

### 将已有用户设为管理员

```powershell
cd backend
python manage.py shell
```

```python
from apps.accounts.models import User

user = User.objects.get(username="用户名")
user.role = User.Role.ADMIN
user.is_staff = True
user.save()
```

退出 Shell 后让该用户重新登录。

## 管理员工作台

管理员工作台包含四个页签：

| 模块 | 功能 |
| --- | --- |
| 题目 | 搜索、分页、新建、编辑和删除 |
| 标签 | 新建、重命名和删除 |
| 测试点 | 按题目筛选，维护输入、输出、分值、顺序和样例状态 |
| 公告 | 新建、编辑、删除、发布和置顶 |

前端会隐藏普通用户的管理入口，但安全控制最终由 Django API 完成。普通用户直接调用写接口仍会收到 `403 Forbidden`。

删除题目会级联删除相关测试点、提交和题解，操作前应确认数据。

## 常用 API

### 认证和个人中心

```text
POST  /api/auth/register/
POST  /api/auth/login/
POST  /api/auth/token/refresh/
GET   /api/auth/me/
PATCH /api/auth/me/
POST  /api/auth/change-password/
GET   /api/auth/me/stats/
```

### 题目、标签和测试点

```text
GET    /api/problems/
POST   /api/problems/                 管理员
GET    /api/problems/{id}/
PATCH  /api/problems/{id}/            管理员
DELETE /api/problems/{id}/            管理员

GET    /api/tags/
POST   /api/tags/                     管理员
PATCH  /api/tags/{id}/                管理员
DELETE /api/tags/{id}/                管理员

GET    /api/test-cases/               管理员
POST   /api/test-cases/               管理员
PATCH  /api/test-cases/{id}/          管理员
DELETE /api/test-cases/{id}/          管理员
```

### 提交和判题

```text
POST /api/submissions/
GET  /api/submissions/
GET  /api/submissions/{id}/
```

### 题解、公告和首页

```text
GET/POST    /api/problems/{id}/solutions/
GET/PATCH/DELETE /api/solutions/{id}/

GET    /api/announcements/
POST   /api/announcements/            管理员
PATCH  /api/announcements/{id}/       管理员
DELETE /api/announcements/{id}/       管理员

GET /api/home/
```

### AI 提交分析

```text
POST /api/ai-agent/runs/
GET  /api/ai-agent/runs/
GET  /api/ai-agent/runs/{id}/
```

## 判题状态

```text
PENDING
JUDGING
ACCEPTED
WRONG_ANSWER
TIME_LIMIT_EXCEEDED
RUNTIME_ERROR
COMPILE_ERROR
SYSTEM_ERROR
```

## 测试与检查

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

```powershell
cd frontend
npm run build
```

## 安全说明

- 隐藏测试点不会通过公开题目接口返回。
- C/C++ 已使用 Docker 进行基础隔离和资源限制。
- Python 当前仍在宿主机通过 `subprocess` 执行。
- 当前项目定位为课程设计和学习演示，不应直接部署到公网执行不可信代码。
- 生产环境还需要更严格的容器权限、系统调用限制、任务队列、HTTPS 和密钥管理。

