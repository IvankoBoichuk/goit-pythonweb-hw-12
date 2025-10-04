API Reference
=============

This section provides comprehensive documentation for all API endpoints.

.. toctree::
   :maxdepth: 2

   authentication
   contacts

Overview
--------

The FastAPI Contacts API provides RESTful endpoints for:

* **Authentication**: User registration, login, and profile management
* **Contacts**: CRUD operations for contact management with user isolation

All endpoints (except authentication) require a valid JWT token in the Authorization header:

.. code-block:: http

   Authorization: Bearer <your_access_token>

Base URL
--------

When running locally with Docker Compose:

* **Development**: ``http://localhost:8000``
* **API Base Path**: ``/api``

Rate Limiting
-------------

API endpoints are protected with rate limiting:

* **Authentication endpoints**: 5 requests per minute per IP
* **Profile endpoints**: 10 requests per minute per user
* **Contact endpoints**: Standard rate limits apply per user

Response Format
--------------

All API responses follow a consistent format:

**Success Response** (2xx)::

    {
      "data": { ... },  // Response data
      "message": "Success message"  // Optional
    }

**Error Response** (4xx/5xx)::

    {
      "detail": "Error description",
      "status_code": 400
    }

Status Codes
------------

The API uses standard HTTP status codes:

* **200**: OK - Request successful
* **201**: Created - Resource created successfully
* **400**: Bad Request - Invalid request data
* **401**: Unauthorized - Authentication required or failed
* **403**: Forbidden - Insufficient permissions
* **404**: Not Found - Resource not found
* **409**: Conflict - Resource already exists
* **422**: Unprocessable Entity - Validation error
* **429**: Too Many Requests - Rate limit exceeded
* **500**: Internal Server Error - Server error