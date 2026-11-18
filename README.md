# \# HelpDesk – Enterprise IT Support \& Ticket Management System

# 

# <p align="center">

# 

# \*\*A Role-Based Enterprise IT Service Management Platform with AI-Assisted Ticket Classification\*\*

# 

# Built with Django REST Framework, React, MySQL, Celery, Redis and Google Gemini AI.

# 

# </p>

# 

# <p align="center">

# 

# !\[Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)

# !\[Django](https://img.shields.io/badge/Django-5.1.4-green?logo=django)

# !\[React](https://img.shields.io/badge/React-18-61DAFB?logo=react)

# !\[MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)

# !\[Redis](https://img.shields.io/badge/Redis-7.4-red?logo=redis)

# !\[AI](https://img.shields.io/badge/AI-Google%20Gemini-8E75B2)

# !\[License](https://img.shields.io/badge/License-MIT-blue)

# 

# </p>

# 

# \---

# 

# \## Overview

# 

# HelpDesk is an enterprise-style IT Service Management (ITSM) application designed to centralize internal technical support operations.

# 

# Employees can report technical issues, support engineers can manage and resolve assigned tickets, department managers can monitor their teams, and administrators can oversee the complete support environment.

# 

# The platform combines structured ticket workflows, department-based access control, SLA management, notifications, analytics, a knowledge base and Gemini-powered AI assistance.

# 

# The project follows a modular backend architecture using Django REST Framework and a React-based frontend.

# 

# \## Key Features

# 

# \### 1. Authentication and Access Control

# 

# \- Email-based authentication.

# \- JWT access and refresh token authentication.

# \- Four application roles: Admin, Manager, Engineer and Employee.

# \- Role-Based Access Control (RBAC).

# \- Department-level and object-level data restrictions.

# \- Protected API endpoints.

# 

# \### 2. Ticket Management

# 

# \- Create and track IT support tickets.

# \- Unique ticket references using the `HD-YYYY-NNNNN` format.

# \- Priority and category classification.

# \- Department and support-team routing.

# \- Engineer assignment.

# \- Ticket status transitions.

# \- Ticket history and activity tracking.

# \- Ticket reopening after resolution.

# 

# \### 3. Department and Support Team Management

# 

# \- Create and manage organizational departments.

# \- Assign department managers.

# \- Create support teams within departments.

# \- Add engineers to support teams.

# \- Department-scoped team visibility.

# \- Controlled assignment of support responsibilities.

# 

# \### 4. SLA Management

# 

# \- Configure response and resolution targets.

# \- Define policies based on priority and department.

# \- Track ticket SLA progress.

# \- Pause and resume SLA timers for supported ticket states.

# \- Background SLA monitoring through Celery.

# \- Escalation handling for SLA breaches.

# 

# \### 5. Comments and Attachments

# 

# \- Public ticket discussions.

# \- Internal staff-only notes.

# \- File attachments.

# \- File extension and size validation.

# \- Permission-controlled access to uploaded files.

# 

# \### 6. Notifications

# 

# \- In-app notifications.

# \- Unread notification tracking.

# \- Asynchronous email notification architecture.

# \- Background task processing with Celery and Redis.

# 

# \### 7. Analytics Dashboard

# 

# \- Ticket statistics.

# \- Priority-based ticket distribution.

# \- Department-level insights.

# \- Engineer performance metrics.

# \- Role-scoped dashboard information.

# \- CSV reporting.

# 

# \### 8. Knowledge Base

# 

# \- Create and manage technical support articles.

# \- Draft, published and archived article states.

# \- Reusable troubleshooting instructions.

# \- Ticket-related knowledge article recommendations.

# 

# \### 9. Gemini AI Assistant

# 

# Google Gemini API integration provides advisory AI assistance for support operations.

# 

# Current AI capabilities include:

# 

# \- AI-assisted ticket classification.

# \- Suggested ticket category and priority.

# \- Department recommendations.

# \- Incident summarization.

# \- Troubleshooting suggestions.

# \- Similar resolved-ticket discovery.

# 

# \*\*Important:\*\* AI recommendations are advisory. Authorized users remain responsible for reviewing and applying suggested ticket changes.

# 

# \### 10. Audit and Activity Tracking

# 

# \- Record important application activities.

# \- Maintain traceability of administrative operations.

# \- Support accountability through audit records.

# 

# \---

# 

# \## Technology Stack

# 

# | Layer | Technologies |

# |---|---|

# | Backend | Python 3.12, Django 5.1.4 |

# | API | Django REST Framework |

# | Authentication | SimpleJWT |

# | Database | MySQL 8 |

# | Frontend | React 18, JavaScript |

# | Build Tool | Vite |

# | Styling | Tailwind CSS |

# | API Communication | Axios |

# | State and Routing | React Hooks, React Router |

# | Form Validation | React Hook Form, Zod |

# | Charts | Recharts |

# | AI Integration | Google Gen AI SDK |

# | Background Tasks | Celery |

# | Message Broker | Redis |

# | API Documentation | drf-spectacular |

# | Testing | Pytest |

# | Deployment Configuration | Docker, Docker Compose, Nginx |

# | CI | GitHub Actions |

# 

# \---

# 

# \## System Architecture

# 

# ```text

# &#x20;                   END USERS

# &#x20;                       |

# &#x20;                       v

# &#x20;             React Frontend (Vite)

# &#x20;                       |

# &#x20;                 REST API Calls

# &#x20;                       |

# &#x20;                       v

# &#x20;             Django REST Framework

# &#x20;                       |

# &#x20;         +-------------+-------------+

# &#x20;         |             |             |

# &#x20;         v             v             v

# &#x20;    Authentication  Business      RBAC \&

# &#x20;      and JWT        Services    Permissions

# &#x20;         |             |             |

# &#x20;         +-------------+-------------+

# &#x20;                       |

# &#x20;                       v

# &#x20;                  MySQL 8

# &#x20;                       |

# &#x20;      +----------------+----------------+

# &#x20;      |                |                |

# &#x20;      v                v                v

# &#x20;  Redis Cache      Celery Worker    Gemini API

# &#x20;      |                |

# &#x20;      |                v

# &#x20;      |           Background Tasks

# &#x20;      |                |

# &#x20;      +----------------+

# &#x20;                       |

# &#x20;                       v

# &#x20;                 Celery Beat

# &#x20;               SLA Monitoring

# ```

# 

# The application uses a modular monolith architecture, separating business responsibilities into Django applications while maintaining a centralized backend.

# 

# \## Role-Based Access Control

# 

# HelpDesk supports four primary roles.

# 

# | Role | Responsibilities |

# |---|---|

# | ADMIN | System-wide administration and management |

# | MANAGER | Manage department-level support operations |

# | ENGINEER | Work on assigned tickets and support-team tickets |

# | EMPLOYEE | Create and track personal support tickets |

# 

# \### Permission Examples

# 

# \*\*Admin\*\*

# \- Access system-wide records.

# \- Manage departments, users and teams.

# \- Manage SLA policies.

# \- Monitor analytics and audit activities.

# 

# \*\*Manager\*\*

# \- View department-specific users and teams.

# \- View department tickets.

# \- Assign tickets within the department.

# \- Monitor department support operations.

# \- View relevant SLA policies.

# 

# \*\*Engineer\*\*

# \- View assigned and eligible support-team tickets.

# \- Update ticket status.

# \- Add public comments and internal notes.

# \- Resolve assigned tickets.

# 

# \*\*Employee\*\*

# \- Create support requests.

# \- Select the responsible support department.

# \- View personal tickets.

# \- Add public comments.

# \- Reopen resolved tickets.

# 

# Backend permissions enforce access restrictions rather than relying only on frontend navigation.

# 

# \---

# 

# \## Ticket Lifecycle

# 

# A typical support workflow:

# 

# ```text

# Employee Creates Ticket

# &#x20;         |

# &#x20;         v

# &#x20;  Ticket Created

# &#x20;         |

# &#x20;         v

# &#x20;Department Routing

# &#x20;         |

# &#x20;         v

# &#x20;Engineer Assignment

# &#x20;         |

# &#x20;         v

# &#x20;   In Progress

# &#x20;         |

# &#x20;         v

# &#x20;Investigation and Comments

# &#x20;         |

# &#x20;         v

# &#x20;     Resolved

# &#x20;         |

# &#x20;         v

# &#x20;Employee Verification

# &#x20;         |

# &#x20;         v

# &#x20;      Closed

# ```

# 

# Tickets can also be placed on hold or reopened according to the supported workflow.

# 

# \---

# 

# \## Project Structure

# 

# ```text

# HelpDesk/

# │

# ├── backend/

# │   ├── apps/

# │   │   ├── accounts/

# │   │   ├── ai\_assistant/

# │   │   ├── analytics/

# │   │   ├── audit/

# │   │   ├── comments/

# │   │   ├── departments/

# │   │   ├── knowledge\_base/

# │   │   ├── notifications/

# │   │   ├── sla/

# │   │   ├── teams/

# │   │   └── tickets/

# │   │

# │   ├── common/

# │   ├── config/

# │   ├── tests/

# │   ├── manage.py

# │   ├── requirements/

# │   └── .env.example

# │

# ├── frontend/

# │   ├── src/

# │   ├── public/

# │   ├── package.json

# │   └── .env.example

# │

# ├── nginx/

# ├── .github/

# ├── docker-compose.yml

# ├── .gitignore

# └── README.md

# ```

# 

# \---

# 

# \## Installation and Local Setup

# 

# \### Prerequisites

# 

# Install the following before starting:

# 

# \- Python 3.12

# \- Node.js and npm

# \- MySQL 8

# \- Redis

# \- Git

# 

# Docker is optional for the containerized setup.

# 

# \### 1. Clone the Repository

# 

# ```cmd

# git clone https://github.com/YOUR-GITHUB-USERNAME/YOUR-REPOSITORY-NAME.git

# 

# cd YOUR-REPOSITORY-NAME

# ```

# 

# Replace the repository URL with the actual GitHub repository after publishing.

# 

# \### 2. Create the MySQL Database

# 

# Open MySQL CLI:

# 

# ```sql

# CREATE DATABASE helpdesk\_db

# CHARACTER SET utf8mb4

# COLLATE utf8mb4\_unicode\_ci;

# 

# CREATE USER 'helpdesk\_user'@'localhost'

# IDENTIFIED BY 'your\_strong\_password';

# 

# GRANT ALL PRIVILEGES ON helpdesk\_db.\*

# TO 'helpdesk\_user'@'localhost';

# 

# FLUSH PRIVILEGES;

# ```

# 

# Use your own secure database password.

# 

# \### 3. Backend Setup

# 

# Open CMD in the project root:

# 

# ```cmd

# cd backend

# 

# py -3.12 -m venv venv

# 

# venv\\Scripts\\python.exe -m pip install --upgrade pip

# 

# venv\\Scripts\\python.exe -m pip install -r requirements\\development.txt

# ```

# 

# Create the environment file:

# 

# ```cmd

# copy .env.example .env

# ```

# 

# Open `.env` and configure:

# 

# \- Django secret key.

# \- MySQL database credentials.

# \- Redis connection settings.

# \- Gemini API key.

# \- Allowed hosts and CORS settings.

# 

# Never commit your actual `.env` file.

# 

# Apply existing migrations:

# 

# ```cmd

# venv\\Scripts\\python.exe manage.py migrate

# ```

# 

# Create an administrator account:

# 

# ```cmd

# venv\\Scripts\\python.exe manage.py createsuperuser

# ```

# 

# Start the backend:

# 

# ```cmd

# venv\\Scripts\\python.exe manage.py runserver 127.0.0.1:8000

# ```

# 

# Backend address:

# 

# `http://127.0.0.1:8000/`

# 

# \### 4. Frontend Setup

# 

# Open another CMD window:

# 

# ```cmd

# cd frontend

# 

# npm install

# 

# copy .env.example .env

# 

# npm run dev

# ```

# 

# Open the frontend URL displayed by Vite in your terminal.

# 

# The default Vite development port is usually `5173`.

# 

# \### 5. Background Services

# 

# Redis must be running before starting Celery services.

# 

# Open separate backend terminal windows.

# 

# Celery worker:

# 

# ```cmd

# cd backend

# 

# venv\\Scripts\\celery.exe -A config worker --loglevel=info --pool=solo

# ```

# 

# Celery Beat:

# 

# ```cmd

# cd backend

# 

# venv\\Scripts\\celery.exe -A config beat --loglevel=info

# ```

# 

# These services support background tasks and scheduled SLA monitoring.

# 

# \---

# 

# \## Environment Variables

# 

# Configuration is managed through environment files.

# 

# \### Backend

# 

# See `backend/.env.example`.

# 

# Important variables include:

# 

# | Variable | Purpose |

# |---|---|

# | DJANGO\_SECRET\_KEY | Django security key |

# | DJANGO\_DEBUG | Development/debug setting |

# | MYSQL\_DATABASE | MySQL database name |

# | MYSQL\_USER | Database username |

# | MYSQL\_PASSWORD | Database password |

# | MYSQL\_HOST | Database host |

# | MYSQL\_PORT | Database port |

# | REDIS\_URL | Redis connection |

# | CELERY\_BROKER\_URL | Celery message broker |

# | GEMINI\_API\_KEY | Google Gemini API key |

# | GEMINI\_MODEL | Gemini model selection |

# | GEMINI\_TIMEOUT\_SECONDS | AI request timeout |

# 

# The current working AI configuration used during development is:

# 

# ```env

# GEMINI\_MODEL=gemini-3.5-flash-lite

# GEMINI\_TIMEOUT\_SECONDS=60

# ```

# 

# Use a valid Gemini API key from Google AI Studio.

# 

# \### Frontend

# 

# See `frontend/.env.example`.

# 

# ```env

# VITE\_API\_BASE\_URL=/api/v1

# ```

# 

# The Gemini API key must remain on the backend. Never expose it through frontend environment variables.

# 

# \---

# 

# \## API Documentation

# 

# HelpDesk exposes REST API endpoints through Django REST Framework.

# 

# With the backend running, access:

# 

# | Resource | URL |

# |---|---|

# | Swagger UI | http://127.0.0.1:8000/api/docs/ |

# | ReDoc | http://127.0.0.1:8000/api/redoc/ |

# | OpenAPI Schema | http://127.0.0.1:8000/api/schema/ |

# | Health Check | http://127.0.0.1:8000/api/v1/health/ |

# | Django Admin | http://127.0.0.1:8000/admin/ |

# 

# API base path:

# 

# ```text

# /api/v1/

# ```

# 

# \---

# 

# \## Testing

# 

# \### Backend Tests

# 

# From the project root:

# 

# ```cmd

# cd backend

# 

# venv\\Scripts\\python.exe -m pytest -q

# ```

# 

# The backend test suite previously completed with \*\*26 passing tests\*\* during development.

# 

# Run the tests again after making changes to verify the current codebase.

# 

# \### Frontend Build

# 

# ```cmd

# cd frontend

# 

# npm run build

# ```

# 

# \### Frontend Lint

# 

# ```cmd

# npm run lint

# ```

# 

# \---

# 

# \## Docker Deployment

# 

# The project includes Docker Compose and Nginx deployment configuration.

# 

# First, configure the backend environment file:

# 

# ```cmd

# copy backend\\.env.example backend\\.env

# ```

# 

# Review the production configuration carefully. Use secure secrets, production database settings, appropriate allowed hosts, and HTTPS configuration.

# 

# Build and start the containers:

# 

# ```cmd

# docker compose up -d --build

# ```

# 

# Create the administrator account:

# 

# ```cmd

# docker compose exec backend python manage.py createsuperuser

# ```

# 

# Check container status:

# 

# ```cmd

# docker compose ps

# ```

# 

# The configured Nginx service is intended to serve the application through the deployment entry point.

# 

# \*\*Note:\*\* Actual production deployment requires infrastructure, DNS, HTTPS, persistent storage and production security configuration.

# 

# \---

# 

# \## Security Considerations

# 

# Security is an important part of this project.

# 

# \- JWT-based authentication.

# \- Server-side role and permission enforcement.

# \- Department-level data access restrictions.

# \- Environment-based secret management.

# \- Password hashing.

# \- Protected attachment access.

# \- File validation.

# \- Staff-only internal ticket notes.

# \- Backend validation of ticket operations.

# \- Audit logging.

# 

# Do not upload API keys, database passwords, private credentials, user records or production data to GitHub.

# 

# \---

# 

# \## Future Enhancements

# 

# Potential improvements for future versions:

# 

# \- Real-time ticket updates using WebSockets.

# \- Corporate Single Sign-On using OAuth2 or OIDC.

# \- Advanced SLA business-hour and holiday calendars.

# \- Customer satisfaction surveys.

# \- Enhanced AI retrieval using approved Knowledge Base articles.

# \- Cloud object storage for attachments.

# \- Production monitoring and observability.

# 

# \---

# 

# \## Learning Outcomes

# 

# This project demonstrates practical experience with:

# 

# \- Full-stack application development.

# \- REST API design and integration.

# \- Database design and ORM operations.

# \- Authentication and authorization.

# \- Role-based access control.

# \- Enterprise workflow implementation.

# \- Background task processing.

# \- AI API integration.

# \- Automated backend testing.

# \- Docker-based deployment configuration.

# 

# \---

# 

# \## Author

# 

# \*\*Yashwanth K\*\*

# 

# Python Full Stack Developer | Backend Development | Generative AI

# 

# \- GitHub: https://github.com/Yashwanth-12-yash

# \- LinkedIn: https://www.linkedin.com/in/yashwanthk2004/

# 

# \---

# 

# 

