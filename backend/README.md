# KouOJ Backend

这是 KouOJ 的 Django 后端初版，目标是先跑通一个最小 Online Judge 闭环：

- 用户注册、登录、获取当前用户
- 管理员通过 Django Admin 写题、维护标签和测试点
- 用户查看题目列表、题目详情
- 用户提交 Python3 代码
- Judge Worker 使用 `subprocess.run()` 执行代码并回写结果

## 1. 准备 Python 环境

建议固定使用一个环境，不要 Windows 和 WSL 混用同一个 `.venv`。

Windows PowerShell 示例：

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

如果你使用 WSL，请在 WSL 里重新创建虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. 创建 MySQL 数据库

进入 MySQL 后执行：

```sql
CREATE DATABASE kouoj DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

默认配置会连接：

```text
HOST: 127.0.0.1
PORT: 3306
DB:   kouoj
USER: root
PASS: 空
```

如果你的密码不是空，可以在启动前设置环境变量。

PowerShell：

```powershell
$env:KOUOJ_DB_PASSWORD="你的MySQL密码"
```

也可以设置这些变量：

```text
KOUOJ_DB_NAME
KOUOJ_DB_USER
KOUOJ_DB_PASSWORD
KOUOJ_DB_HOST
KOUOJ_DB_PORT
```

临时不用 MySQL、只想先检查 Django 是否能跑时，可以用 SQLite：

```powershell
$env:KOUOJ_USE_SQLITE="1"
```

## 3. 初始化数据库

在 `backend` 目录执行：

```powershell
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## 4. 启动后端

```powershell
python manage.py runserver
```

后端地址：

```text
http://127.0.0.1:8000/
```

后台管理：

```text
http://127.0.0.1:8000/admin/
```

## 5. 启动判题 Worker

另开一个终端，进入同一个虚拟环境和 `backend` 目录：

```powershell
python manage.py run_judge
```

只处理一次任务可以用：

```powershell
python manage.py run_judge --once
```

## 6. 当前 API

认证：

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/token/refresh/
GET  /api/auth/me/
```

题目：

```text
GET    /api/problems/
GET    /api/problems/{id}/
POST   /api/problems/          管理员
PUT    /api/problems/{id}/     管理员
DELETE /api/problems/{id}/     管理员
```

标签：

```text
GET  /api/tags/
POST /api/tags/                管理员
```

提交：

```text
POST /api/submissions/
GET  /api/submissions/
GET  /api/submissions/{id}/
```

提交代码示例：

```json
{
  "problem": 1,
  "language": "python3",
  "code": "a, b = map(int, input().split())\nprint(a + b)"
}
```

## 7. 第一题建议

可以先在 Django Admin 创建一道 A+B：

题目标题：

```text
A+B Problem
```

样例测试点：

```text
input_data:
1 2

output_data:
3
```

再加一个隐藏测试点：

```text
input_data:
10 20

output_data:
30
```
