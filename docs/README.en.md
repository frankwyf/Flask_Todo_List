# Detailed Guide (English)

## 1. Project Purpose
This project is a Flask-based task manager designed as a portfolio-quality open-source sample. It supports:
- Account registration and login
- Task CRUD (create, update, complete, undo, delete)
- Filtering/search by status, module, and title
- Lightweight visualization using ECharts
- Optional email reminder and optional weather widget integration

## 2. Tech Stack
- Backend: Flask, SQLAlchemy, Flask-Migrate
- Auth/Security: Flask-Bcrypt
- Frontend: Jinja2 templates, Bootstrap, jQuery, ECharts
- Database: SQLite by default, configurable with DATABASE_URL

## 3. Runtime Architecture
- Entry point: run.py
- App bootstrap: app/__init__.py
- Configuration: app/config.py
- Data models: app/model.py
- Route handlers: app/view.py
- Templates/static assets: app/templates, app/static

Request flow:
1. Browser sends request to Flask route in app/view.py
2. Route reads/writes model data via SQLAlchemy
3. Route renders Jinja template with task/user data
4. Template + static JS/CSS produce final UI and interaction

## 4. Configuration Strategy
All sensitive values are loaded from environment variables instead of source code.

Important variables:
- SECRET_KEY: Flask session secret
- DATABASE_URL: SQLAlchemy database URI
- MAIL_*: Optional email reminder service
- WEATHER_WIDGET_KEY: Optional weather widget

Default behavior:
- If DATABASE_URL is not set, project uses SQLite at instance/app.db.
- If MAIL settings are empty, email reminders will not work until configured.
- If WEATHER_WIDGET_KEY is empty, weather widget remains disabled.

## 5. Data Model Details
### Todoers
- id: primary key
- username: unique username
- password: bcrypt hash string
- Email: user email
- status: online/offline flag

### Task
- taskID: primary key
- module: logical category
- assessment: task title
- create_date: creation datetime
- ddl: deadline datetime
- remind: reminder datetime
- description: free text description
- priority: 1~4
- status: 0/1 uncompleted/completed
- host: foreign key to Todoers.id

## 6. Security and Desensitization Notes
Implemented in this open-source version:
- Removed hardcoded database credentials
- Removed hardcoded SMTP account and password
- Removed hardcoded weather API key
- Removed personal name/student-id/email references from templates
- Added .gitignore and .env.example to prevent accidental secret commits

## 7. Common Technical Q&A
### Q1: Why app factory style?
App factory allows cleaner config management, easier testing, and safer initialization order for extensions.

### Q2: Why SQLite by default?
It minimizes setup friction for contributors and reviewers. Production can switch to MySQL/PostgreSQL via DATABASE_URL.

### Q3: Why still keep old route names?
To preserve compatibility with existing templates and JavaScript behavior while improving project safety and portability.

### Q4: What is the quickest local smoke test?
1. Create and activate virtual environment
2. Install requirements
3. Run python run.py
4. Open http://127.0.0.1:5000/
5. Register user, add task, complete task, edit task

## 8. Suggested Next Improvements
- Introduce Flask Blueprints to split route modules
- Add automated tests (pytest) for auth and task routes
- Add CSRF and form validation with Flask-WTF forms
- Add Dockerfile + docker-compose for 1-command startup
- Add GitHub Actions for lint/test pipeline
