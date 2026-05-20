# AGENT.md

# 项目简介

本项目是一个简化版 Online Judge（OJ）系统。

项目用途：

- 数据库课程设计
- Python 课程设计
- 实习简历项目
- 全栈开发学习

项目目标：

实现一个“功能完整但不过度复杂”的小型 OJ 系统。

当前阶段重点：

- 能运行
- 能演示
- 能答辩
- 代码结构清晰
- 易于理解和维护

当前不是工业级 OJ。

不要过度设计。

**注意：我需要通过边学边做来体验一个完整项目的架构设计，所以所有提问的操作请你不要一股脑都给我写好，而是指引我自己来创建架构，写代码**
---

# 技术栈

## 后端

- Python
- Django
- Django REST Framework
- MySQL
- JWT 鉴权

## 前端

- Vue3
- TypeScript
- Vite
- Element Plus

## 判题模块

当前版本：

- Python subprocess

后续可升级：

- Docker 沙箱
- 多语言支持

---

# 项目架构

系统结构：

Vue Frontend
↓
Django REST API
↓
MySQL
↓
Judge Worker
↓
返回判题结果

---

# 当前开发目标（MVP）

当前优先实现：

1. 用户注册登录
2. JWT 鉴权
3. 题目列表
4. 题目详情
5. 标签分类
6. 提交代码
7. 自动判题
8. 提交记录

完成以上功能即可认为第一版完成。

---

# 当前阶段禁止事项

除非明确要求，否则不要主动引入：

- Redis
- Celery
- Kafka
- RabbitMQ
- Kubernetes
- 微服务
- WebSocket
- 分布式判题
- 高并发架构
- Docker 集群

当前阶段：

优先简单、可运行。

---

# 后端目录结构

backend/
    manage.py

    config/

    apps/
        accounts/
        problems/
        submissions/
        judge/

    utils/

---

# 前端目录结构

frontend/
    src/
        api/
        router/
        stores/
        views/
        components/
        types/

---

# Django 开发规则

## ORM

必须使用 Django ORM。

优先：

- 可读性
- 易理解

避免：

- 复杂 ORM 技巧
- 难理解查询
- 过度优化

---

## API 风格

使用 RESTful API。

示例：

GET /api/problems/
GET /api/problems/{id}/
POST /api/submissions/

---

## View 规则

不要把大量业务逻辑直接写在 View 中。

复杂逻辑拆分到：

- services
- utils
- judge worker

---

# 数据库设计

当前核心表：

## User

基于：

AbstractUser

扩展字段：

- role
- solved_count
- submit_count

---

## Problem

字段：

- title
- description
- input_description
- output_description
- difficulty
- time_limit
- memory_limit
- is_public

---

## Tag

标签表。

Problem 与 Tag 为多对多关系。

---

## TestCase

字段：

- input_data
- output_data
- is_sample

当前阶段：

测试数据允许直接存数据库。

---

## Submission

字段：

- user
- problem
- language
- code
- status
- time_used
- memory_used
- error_message

---

# 判题系统规则

当前版本：

只支持 Python3。

---

# 判题流程

Judge Worker 工作流程：

1. 获取 Pending 提交
2. 修改状态为 Judging
3. 查询测试点
4. 执行用户代码
5. 获取 stdout / stderr
6. 对比标准输出
7. 更新提交状态
8. 保存判题结果

---

# subprocess 规则

禁止：

- exec()
- eval()

必须：

- subprocess.run()
- timeout
- 捕获 stdout
- 捕获 stderr

示例：

```python
subprocess.run(..., timeout=2)
```

---

# 当前安全策略

当前版本允许：

“本地 subprocess 判题”

但必须：

- 设置 timeout
- 不部署公网
- 不允许陌生用户访问

后续可升级：

Docker 沙箱。

---

# 前端开发规则

## UI 风格

要求：

- 简洁
- 清晰
- 易用

推荐：

- Element Plus

避免：

- 复杂动画
- 花哨特效

---

# 页面规划

当前必须实现：

/login
/register
/problems
/problems/:id
/submissions
/submissions/:id

---

# 题目详情页

页面包含：

左侧：

- 题目描述
- 输入描述
- 输出描述
- 样例

右侧：

- 语言选择
- 代码编辑器
- 提交按钮
- 判题结果

---

# 代码编辑器

当前阶段：

允许使用 textarea。

后续可升级：

Monaco Editor。

---

# Agent 代码生成规则

开发者是新手。

生成代码时：

必须：

- 注重可读性
- 注重解释
- 注重学习成本

优先：

- 清晰
- 简单
- 易懂
- 可运行

避免：

- 炫技
- 复杂设计模式
- 过度封装
- 高级元编程

---

# Agent 输出要求

生成代码时必须说明：

1. 文件位置
2. 文件作用
3. 请求流程
4. 数据关系
5. 如何运行

不要只给代码。

---

# 文档要求

生成新模块时：

需要补充：

- README
- API 文档
- 数据库说明
- 接口说明

---

# 开发原则

遵循：

“小步开发”

不要一次生成整个大型系统。

正确顺序：

1. 注册登录
2. 题目系统
3. 提交系统
4. 判题系统

---

# 优先级规则

始终优先：

1. 功能完整
2. 可运行
3. 可理解
4. 可维护

性能优化优先级很低。

---

# 项目最终目标

项目最终需要达到：

- 可以完整演示
- 可以完成课程设计
- 可以写进简历
- 开发者能够理解代码
- 后续可以继续扩展

---

# 当前项目定位

这是：

“适合课程设计与实习简历的新手 OJ 项目”

不是工业级商业系统。

不要过度复杂化。
````
ubprocess.run(..., timeout=2)