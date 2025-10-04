Authentication API
=================

The authentication API handles user registration, login, profile management, and avatar uploads.

.. currentmodule:: src.api.auth

Endpoints
---------

User Registration
~~~~~~~~~~~~~~~~

.. http:post:: /api/auth/register

   Register a new user account.

   **Rate Limited**: 5 requests per minute per IP

   **Request Body**:

   .. code-block:: json

      {
        "username": "string",
        "email": "user@example.com", 
        "password": "string",
        "full_name": "string"  // optional
      }

   **Response** (201 Created):

   .. code-block:: json

      {
        "id": 1,
        "username": "testuser",
        "email": "user@example.com",
        "full_name": "Test User",
        "is_active": true,
        "avatar_url": null
      }

   **Errors**:
   
   * **409 Conflict**: Username or email already registered
   * **422 Validation Error**: Invalid input data

User Login
~~~~~~~~~

.. http:post:: /api/auth/login

   Authenticate user and receive access token.

   **Rate Limited**: 5 requests per minute per IP

   **Request Body**:

   .. code-block:: json

      {
        "username": "string",
        "password": "string"
      }

   **Response** (200 OK):

   .. code-block:: json

      {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer"
      }

   **Errors**:
   
   * **401 Unauthorized**: Invalid credentials
   * **404 Not Found**: User not found

Get Current User
~~~~~~~~~~~~~~~

.. http:get:: /api/auth/me

   Get current authenticated user information.

   **Rate Limited**: 10 requests per minute per user

   **Headers**: ``Authorization: Bearer <token>``

   **Response** (200 OK):

   .. code-block:: json

      {
        "id": 1,
        "username": "testuser", 
        "email": "user@example.com",
        "full_name": "Test User",
        "is_active": true,
        "avatar_url": "https://cloudinary.com/image/avatar.jpg"
      }

Avatar Management
~~~~~~~~~~~~~~~~

.. http:post:: /api/auth/avatar

   Upload user avatar image.

   **Headers**: 
   
   * ``Authorization: Bearer <token>``
   * ``Content-Type: multipart/form-data``

   **Request Body**: Form data with ``file`` field containing image

   **Response** (200 OK):

   .. code-block:: json

      {
        "avatar_url": "https://cloudinary.com/image/avatar.jpg"
      }

   **Errors**:
   
   * **400 Bad Request**: Invalid file format or size
   * **401 Unauthorized**: Authentication required

.. http:delete:: /api/auth/avatar

   Delete user avatar image.

   **Headers**: ``Authorization: Bearer <token>``

   **Response** (200 OK):

   .. code-block:: json

      {
        "message": "Avatar deleted successfully"
      }

Email Verification
~~~~~~~~~~~~~~~~~

.. http:get:: /api/auth/verify/{token}

   Verify user email address using verification token.

   **Parameters**:
   
   * ``token`` (string): Email verification token from registration email

   **Response** (200 OK):

   .. code-block:: json

      {
        "message": "Email verified successfully"
      }

   **Errors**:
   
   * **400 Bad Request**: Invalid or expired token
   * **404 Not Found**: User not found

Security Notes
--------------

**Password Requirements**:
* Passwords are hashed using PBKDF2-SHA256
* No minimum length enforced at API level (implement in frontend)

**Token Security**:
* JWT tokens expire after 30 minutes (configurable)
* Include user ID in token payload
* Signed with SECRET_KEY (must be changed in production)

**Avatar Uploads**:
* Supported formats: JPEG, PNG, GIF, WebP
* Maximum file size: 5MB (configurable)
* Images uploaded to Cloudinary (requires configuration)

**Rate Limiting**:
* Applied per IP address for registration/login
* Applied per authenticated user for profile operations
* Uses Redis backend with in-memory fallback