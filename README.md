# 🎫 HelpDesk – IT Support & Ticket Management System

\<p align="center">   \<strong>An enterprise-style IT HelpDesk platform for managing support tickets, teams, departments, SLAs, and AI-powered assistance.\</strong> \</p>

\<p align="center">   \<img src="[https://img.shields.io/badge/Python-3.12-blue?logo=python](https://img.shields.io/badge/Python-3.12-blue?logo=python)" alt="Python"/>   \<img src="[https://img.shields.io/badge/Django-5.1.4-green?logo=django](https://img.shields.io/badge/Django-5.1.4-green?logo=django)" alt="Django"/>   \<img src="[https://img.shields.io/badge/React-18-61DAFB?logo=react](https://img.shields.io/badge/React-18-61DAFB?logo=react)" alt="React"/>   \<img src="[https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)" alt="MySQL"/>   \<img src="[https://img.shields.io/badge/AI-Google%20Gemini-blueviolet](https://img.shields.io/badge/AI-Google%20Gemini-blueviolet)" alt="Google Gemini"/> \</p>

\<p align="center">   \<a href="[https://github.com/Yashwanth-12-yash/helpdesk-it-support-system](https://github.com/Yashwanth-12-yash/helpdesk-it-support-system)">GitHub Repository\</a> \</p>

---

## 📌 Overview

HelpDesk is a full-stack IT Support and Ticket Management System designed to simplify how organizations handle internal technical support requests.

Employees can raise support tickets, track their progress, communicate with support engineers, and access knowledge-base resources. Administrators and managers can manage users, departments, teams, service-level agreements, and support operations.

The platform also integrates Google Gemini AI to provide AI-assisted support.

The application is built using Django REST Framework, React, MySQL, and modern backend technologies.

## ✨ Key Features

### 🎫 Ticket Management

- Create, update, assign, and track support tickets.
- Manage ticket priorities and statuses.
- View ticket details and activity.
- Support ticket lifecycle management.

### 👥 User Roles & Access Control

- Role-based access control (RBAC).
- Four user roles:
  - ADMIN
  - MANAGER
  - ENGINEER
  - EMPLOYEE
- Department- and team-based access restrictions.

### 🏢 Department & Team Management

- Create and manage departments.
- Organize support engineers into teams.
- Assign tickets according to organizational structure.

### 💬 Comments & Attachments

- Public and internal ticket comments.
- Upload and manage ticket attachments.
- Maintain communication between employees and support teams.

### ⏱️ SLA Management

- Configure service-level agreements.
- Monitor ticket response and resolution deadlines.
- Support SLA tracking and escalation workflows.

### 🤖 AI-Powered Assistance

- Google Gemini API integration.
- AI-assisted support responses.
- AI functionality integrated into the HelpDesk workflow.

### 📚 Knowledge Base

- Maintain support articles and resources.
- Provide reusable information for common technical issues.

### 🔔 Notifications

- Ticket-related notifications.
- Email notification functionality.
- Background task processing with Celery.

### 📊 Analytics & Audit Logs

- Support activity analytics.
- Track important system operations.
- Maintain audit records for accountability.

---

## 🛠️ Technology Stack

| Category                 | Technologies                  |
| ------------------------ | ----------------------------- |
| Frontend                 | React 18, JavaScript, Vite    |
| Styling                  | Tailwind CSS                  |
| Backend                  | Python, Django 5.1.4          |
| API                      | Django REST Framework         |
| Authentication           | JWT, Simple JWT               |
| Database                 | MySQL 8                       |
| AI Integration           | Google Gemini API             |
| Background Tasks         | Celery, Redis                 |
| API Documentation        | drf-spectacular, OpenAPI      |
| Testing                  | Pytest                        |
| Deployment Configuration | Docker, Docker Compose, Nginx |
| Version Control          | Git, GitHub                   |

---

## 🏗️ System Architecture

```text
              ┌──────────────────────────┐
              │       React Frontend     │
              │       JavaScript         │
              └────────────┬─────────────┘
                           │
                      REST API
                           │
              ┌────────────▼─────────────┐
              │       Django Backend     │
              │   Django REST Framework │
              └────────────┬─────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌──────▼──────┐  ┌──────▼──────┐
    │   MySQL   │   │ Google      │  │ Celery +   │
    │ Database  │   │ Gemini API  │  │ Redis      │
    └───────────┘   └─────────────┘  └─────────────┘
```

---

## 📂 Project Structure

```text
helpdesk-it-support-system/
│
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── ai_assistant/
│   │   ├── analytics/
│   │   ├── audit/
│   │   ├── comments/
│   │   ├── departments/
│   │   ├── knowledge_base/
│   │   ├── notifications/
│   │   ├── sla/
│   │   ├── teams/
│   │   └── tickets/
│   │
│   ├── common/
│   ├── config/
│   ├── requirements/
│   ├── tests/
│   ├── manage.py
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   └── utils/
│   │
│   └── package.json
│
├── nginx/
├── .github/
│   └── workflows/
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## ⚙️ Installation & Setup

### Prerequisites

Install the following before running the project:

- Python 3.12
- Node.js and npm
- MySQL 8
- Redis
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Yashwanth-12-yash/helpdesk-it-support-system.git
```

```bash
cd helpdesk-it-support-system
```

### 2. Backend Setup

Open a terminal in the project root.

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements/development.txt
```

### 3. Configure Environment Variables

Create your local environment file using the example:

```cmd
copy .env.example .env
```

Open `backend/.env` and configure your local settings, including:

- Django secret key
- Database name
- Database username and password
- Google Gemini API key
- Redis configuration

**Important:** Never upload your actual `.env` file or API keys to GitHub.

### 4. Database Setup

Create a MySQL database:

```sql
CREATE DATABASE helpdesk_db;
```

Configure the database credentials in your environment file.

Apply migrations:

```bash
python manage.py migrate
```

Create an administrator account:

```bash
python manage.py createsuperuser
```

### 5. Start the Backend

```bash
python manage.py runserver
```

Backend:

```text
http://127.0.0.1:8000/
```

### 6. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install frontend dependencies:

```bash
npm install
```

Create the frontend environment file:

```cmd
copy .env.example .env
```

Start the development server:

```bash
npm run dev
```

Open the frontend URL displayed in your terminal.

---

## 🧪 Testing

The backend includes automated tests covering important application workflows.

Run the test suite from the backend directory:

```bash
pytest
```

The latest recorded test run completed with **26 passed tests**.

Test coverage includes:

- Authentication
- Role-based access control
- Ticket management
- Department and team workflows
- Comments and attachments
- SLA functionality
- Analytics, knowledge base, and AI workflows

---

## 📖 API Documentation

The backend uses Django REST Framework and drf-spectacular for API documentation.

When the backend is running, check the configured API documentation routes:

- Swagger UI: `/api/docs/`
- OpenAPI schema: `/api/schema/`

The exact availability depends on the backend URL configuration.

---

## 🐳 Docker

The repository includes Docker and Docker Compose configuration for containerized application setup.

Review `docker-compose.yml` and the environment configuration before starting the services.

```bash
docker compose config
```

Start configured services:

```bash
docker compose up --build
```

Stop services:

```bash
docker compose down
```

---

## 🔐 Security Considerations

- JWT-based authentication.
- Role-based authorization.
- Department and team-level access restrictions.
- Environment-based configuration for sensitive credentials.
- Git ignore rules for local environment files and generated files.

Never commit production secrets, API keys, database passwords, or private credentials.

---

## 🚀 Future Improvements

- Cloud deployment.
- Real-time ticket updates.
- Advanced analytics and reporting.
- Enhanced AI-powered ticket classification.
- Expanded automated test coverage.

---

## 🎯 What This Project Demonstrates

This project demonstrates practical experience in:

- Full-stack web application development.
- REST API development using Django REST Framework.
- React frontend integration.
- Database design and MySQL operations.
- JWT authentication and role-based authorization.
- Background task processing.
- Third-party AI API integration.
- Automated backend testing.
- Docker-based application configuration.

---

## 👨‍💻 Author

**Yashwanth K**

Python Full Stack Developer | AI/ML Enthusiast

- GitHub: [https://github.com/Yashwanth-12-yash](https://github.com/Yashwanth-12-yash)
- LinkedIn: [https://www.linkedin.com/in/yashwanthk2004/](https://www.linkedin.com/in/yashwanthk2004/)

---

\<p align="center">   \<strong>Built to make IT support management more organized, efficient, and intelligent.\</strong> \</p>
