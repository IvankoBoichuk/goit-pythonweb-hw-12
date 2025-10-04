FastAPI Contacts API Documentation
====================================

Welcome to the FastAPI Contacts API documentation. This application provides a secure contact management system with JWT authentication, rate limiting, and PostgreSQL database backend.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   overview
   quickstart
   api/index
   modules/index

Features
--------

* **JWT Authentication**: Secure user authentication with access tokens
* **Rate Limiting**: Protection against abuse with Redis-backed rate limiting
* **User Isolation**: Complete data separation between users
* **Email Verification**: User email verification workflow
* **File Uploads**: Avatar upload with Cloudinary integration
* **RESTful API**: Clean REST endpoints with OpenAPI documentation

Architecture Overview
--------------------

The application follows a clean architecture pattern with clear separation of concerns:

* **API Layer** (`src/api/`): FastAPI routers and endpoint definitions
* **Service Layer** (`src/services/`): Business logic and external service integrations
* **Repository Layer** (`src/repository/`): Data access and database operations
* **Database Layer** (`src/database/`): SQLAlchemy models and session management

Quick Start
-----------

1. **Environment Setup**::

    cp .env.example .env
    # Edit .env with your configuration

2. **Docker Development**::

    docker compose up --build

3. **API Access**:
   
   * API: http://localhost:8000
   * Documentation: http://localhost:8000/docs
   * ReDoc: http://localhost:8000/redoc

Authentication Flow
------------------

1. Register a new user with ``POST /api/auth/register``
2. Verify email (if email service is configured)
3. Login with ``POST /api/auth/login`` to get access token
4. Include token in ``Authorization: Bearer <token>`` header for protected endpoints

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`