Code Documentation
==================

This section provides detailed documentation for all modules, classes, and functions in the codebase.

.. toctree::
   :maxdepth: 2

   services
   repository
   database
   api_modules
   schemas
   config

Overview
--------

The codebase is organized into several layers following clean architecture principles:

**Services Layer**
   Business logic, external service integrations, and authentication handling.

**Repository Layer**  
   Data access patterns and database operation abstractions.

**Database Layer**
   SQLAlchemy models and database configuration.

**API Layer**
   FastAPI routers and endpoint definitions.

**Schemas**
   Pydantic models for request/response validation.

**Configuration**
   Application settings and environment variable management.

Code Standards
--------------

**Docstring Format**
   All functions and classes use Google-style docstrings with type hints.

**Async/Await**
   Repository methods use async patterns where applicable for database operations.

**Type Hints**
   Full type annotations for function parameters and return values.

**Error Handling**
   Consistent use of FastAPI's HTTPException for API errors.