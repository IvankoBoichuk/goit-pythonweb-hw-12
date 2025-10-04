Project Overview
================

Architecture
------------

The FastAPI Contacts API is built using a **multi-layered architecture** that promotes separation of concerns and maintainability:

Layer Structure
~~~~~~~~~~~~~~~

**API Layer** (``src/api/``)
   FastAPI routers with authentication decorators and rate limiting. Handles HTTP request/response cycle and input validation.

**Service Layer** (``src/services/``)
   Contains business logic for authentication, contact management, email, and external service integrations (Cloudinary, SMTP).

**Repository Layer** (``src/repository/``)
   Data access layer with async/await patterns. Abstracts database operations from business logic.

**Database Layer** (``src/database/``)
   SQLAlchemy models and session management. Defines data structures and relationships.

Key Design Patterns
~~~~~~~~~~~~~~~~~~

**Repository Pattern**
   All database operations go through repository classes to maintain clean separation between business logic and data access.

**Dependency Injection**
   FastAPI's dependency system is used for database sessions, authentication, and service instances.

**User Context Isolation**
   All data operations are filtered by the authenticated user to prevent cross-user data exposure.

Technology Stack
----------------

Core Framework
~~~~~~~~~~~~~~
* **FastAPI**: Modern Python web framework with automatic OpenAPI documentation
* **SQLAlchemy 2.0**: Python SQL toolkit and ORM with async support
* **PostgreSQL**: Robust relational database for data persistence

Authentication & Security
~~~~~~~~~~~~~~~~~~~~~~~~
* **JWT (JSON Web Tokens)**: Stateless authentication with configurable expiration
* **PBKDF2-SHA256**: Secure password hashing (alternative to bcrypt)
* **Rate Limiting**: Protection with Redis backend and in-memory fallback

External Services
~~~~~~~~~~~~~~~~
* **Redis**: Rate limiting storage and caching
* **Cloudinary**: Image upload and management for user avatars
* **SMTP**: Email verification and notifications

Development Tools
~~~~~~~~~~~~~~~~
* **Docker & Docker Compose**: Containerized development environment
* **Pydantic**: Data validation and serialization
* **python-dotenv**: Environment variable management

Configuration Management
-----------------------

All configuration is centralized in ``src/conf/config.py`` using Pydantic's ``BaseModel``:

* Environment variables loaded with ``python-dotenv``
* Sensible defaults for development
* Type validation and conversion
* CORS, rate limiting, and external service configuration

Security Considerations
----------------------

**Password Security**
   Uses PBKDF2-SHA256 for password hashing with automatic salt generation.

**Token Security**
   JWT tokens are signed with a configurable secret key and include expiration times.

**Rate Limiting**
   Applied to authentication endpoints and sensitive operations to prevent abuse.

**User Data Isolation**
   All contact operations are filtered by the authenticated user's ID to prevent unauthorized access.

**CORS Configuration**
   Configurable CORS settings for cross-origin resource sharing in development and production.