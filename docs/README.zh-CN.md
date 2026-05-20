# 详细说明文档（中文）

## 1. 项目定位
这是一个基于 Flask 的任务管理项目，已整理为可用于个人作品集展示的开源版本，包含：
- 注册与登录
- 任务增删改查
- 按状态/模块/标题筛选
- 基于 ECharts 的简单可视化
- 可选邮件提醒、可选天气组件

## 2. 技术栈
- 后端：Flask、SQLAlchemy、Flask-Migrate
- 鉴权/安全：Flask-Bcrypt
- 前端：Jinja2、Bootstrap、jQuery、ECharts
- 数据库：默认 SQLite，可通过环境变量切换

## 3. 运行结构
- 启动入口：run.py
- 应用初始化：app/__init__.py
- 配置管理：app/config.py
- 数据模型：app/model.py
- 路由逻辑：app/view.py
- 页面与静态资源：app/templates、app/static

请求流程：
1. 浏览器请求进入 app/view.py 的路由
2. 路由通过 SQLAlchemy 操作模型
3. 路由将数据注入模板并渲染页面
4. JS/CSS 完成交互与展示

## 4. 配置与脱敏策略
本开源版将敏感信息全部改为环境变量读取，不再写死在仓库代码中。

关键变量：
- SECRET_KEY
- DATABASE_URL
- MAIL_SERVER / MAIL_PORT / MAIL_USERNAME / MAIL_PASSWORD / MAIL_DEFAULT_SENDER
- WEATHER_WIDGET_KEY

默认行为：
- 未设置 DATABASE_URL 时，使用 instance/app.db（SQLite）
- 未配置 MAIL_* 时，邮件提醒功能保持可选但不可用
- 未配置 WEATHER_WIDGET_KEY 时，天气组件自动关闭

## 5. 数据模型说明
### Todoers
- id：主键
- username：唯一用户名
- password：bcrypt 哈希
- Email：邮箱
- status：在线状态

### Task
- taskID：主键
- module：任务所属模块
- assessment：任务标题
- create_date：创建时间
- ddl：截止时间
- remind：提醒时间
- description：描述
- priority：优先级（1-4）
- status：完成状态（0/1）
- host：外键，关联 Todoers.id

## 6. 技术细节问答（面试/讲解可用）
### 为什么改成环境变量配置？
因为开源仓库不能包含真实密钥或账号；环境变量是最常见、最安全的配置方式之一。

### 为什么默认改成 SQLite？
为了降低上手门槛，评审者无需先安装 MySQL 就能跑起来。

### 为什么没有大改模板和路由命名？
优先保证现有功能稳定，在最小改动下完成“可运行 + 可开源 + 可解释”。后续可再逐步模块化。

## 7. 后续可迭代方向
- 用 Blueprint 重构路由分层
- 补 pytest 自动化测试
- 表单迁移到 Flask-WTF 并增强校验
- 增加 Docker 化部署
- 接入 CI（lint + test）
