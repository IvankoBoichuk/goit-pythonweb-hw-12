Quick Start Guide
================

This guide will help you get the FastAPI Contacts API up and running quickly.

Prerequisites
-------------

* Docker and Docker Compose
* Git (to clone the repository)
* A text editor for configuration

Installation
------------

1. **Clone the Repository**::

    git clone <repository-url>
    cd goit-pythonweb-hw-12

2. **Environment Configuration**::

    cp .env.example .env

   Edit the ``.env`` file with your configuration:

   .. code-block:: bash

      # Required: Change this in production!
      SECRET_KEY=your-secret-key-change-this-in-production
      
      # Database (Docker Compose defaults)
      DATABASE_URL=postgresql+psycopg2://postgres:567234@postgres:5432/hw12
      
      # Optional: External services
      CLOUDINARY_NAME=your-cloudinary-name
      CLOUDINARY_API_KEY=your-api-key
      CLOUDINARY_API_SECRET=your-api-secret
      
      # Email configuration (optional)
      SMTP_SERVER=smtp.gmail.com
      SMTP_PORT=587
      SMTP_USERNAME=your-email@gmail.com
      SMTP_PASSWORD=your-app-password
      FROM_EMAIL=your-email@gmail.com

3. **Start the Application**::

    docker compose up --build

   This will start:
   - PostgreSQL database on port 5432
   - Redis for rate limiting on port 6379
   - FastAPI application on port 8000

4. **Verify Installation**:
   
   Open http://localhost:8000/health in your browser. You should see::

    {"status": "healthy", "database": "connected"}

API Documentation
-----------------

Once the application is running, you can access:

* **Swagger UI**: http://localhost:8000/docs
* **ReDoc**: http://localhost:8000/redoc

Basic Usage
-----------

Register a User
~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/auth/register" \\
     -H "Content-Type: application/json" \\
     -d '{
       "username": "testuser",
       "email": "test@example.com", 
       "password": "password123",
       "full_name": "Test User"
     }'

Login and Get Token
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/auth/login" \\
     -H "Content-Type: application/json" \\
     -d '{
       "username": "testuser",
       "password": "password123"
     }'

Response::

    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "token_type": "bearer"
    }

Create a Contact
~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "http://localhost:8000/api/contacts" \\
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "email": "john@example.com",
       "phone": "+1234567890",
       "birthday": "1990-01-15",
       "additional_info": "Friend from college"
     }'

Get All Contacts
~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X GET "http://localhost:8000/api/contacts" \\
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

Development Workflow
-------------------

Local Development
~~~~~~~~~~~~~~~~

For local development without Docker:

1. **Install Dependencies**::

    pip install -e .
    pip install -e .[dev]  # For development tools

2. **Start Database Services**::

    # Start only PostgreSQL and Redis
    docker compose up postgres redis -d

3. **Update Environment**::

    # Use localhost URLs for local development
    DATABASE_URL=postgresql+psycopg2://postgres:567234@localhost:5432/hw12
    REDIS_URL=redis://localhost:6379

4. **Run Application**::

    uvicorn main:app --reload

Testing Endpoints
~~~~~~~~~~~~~~~~

Use the interactive Swagger UI at http://localhost:8000/docs to:

* Explore all available endpoints
* Test API calls with authentication
* View request/response schemas
* Download OpenAPI specification

Troubleshooting
--------------

**Database Connection Issues**
   Ensure PostgreSQL container is healthy: ``docker compose ps``

**Rate Limiting Errors**
   If Redis is unavailable, the app falls back to in-memory rate limiting

**Authentication Errors**
   Check that the ``Authorization`` header includes ``Bearer`` prefix

**CORS Issues**
   Configure ``CORS_ORIGINS`` in ``.env`` for cross-origin requests

Next Steps
----------

* Read the :doc:`api/index` for detailed endpoint documentation
* Explore :doc:`modules/index` for code-level documentation
* Check the :doc:`overview` for architecture details