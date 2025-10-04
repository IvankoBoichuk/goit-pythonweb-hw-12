Contacts API
============

The contacts API provides CRUD operations for managing personal contacts with complete user isolation.

.. currentmodule:: src.api.contacts

All contact endpoints require authentication and automatically filter results by the authenticated user.

Endpoints
---------

List Contacts
~~~~~~~~~~~~~

.. http:get:: /api/contacts

   Retrieve all contacts for the authenticated user with pagination.

   **Headers**: ``Authorization: Bearer <token>``

   **Query Parameters**:
   
   * ``skip`` (integer, optional): Number of records to skip. Default: 0
   * ``limit`` (integer, optional): Maximum records to return. Default: 100

   **Response** (200 OK):

   .. code-block:: json

      [
        {
          "id": 1,
          "first_name": "John",
          "last_name": "Doe", 
          "email": "john@example.com",
          "phone": "+1234567890",
          "birthday": "1990-01-15",
          "additional_info": "Friend from college"
        }
      ]

Create Contact
~~~~~~~~~~~~~~

.. http:post:: /api/contacts

   Create a new contact for the authenticated user.

   **Headers**: 
   
   * ``Authorization: Bearer <token>``
   * ``Content-Type: application/json``

   **Request Body**:

   .. code-block:: json

      {
        "first_name": "string",
        "last_name": "string", 
        "email": "contact@example.com",
        "phone": "string",
        "birthday": "YYYY-MM-DD",
        "additional_info": "string"  // optional
      }

   **Response** (201 Created):

   .. code-block:: json

      {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com", 
        "phone": "+1234567890",
        "birthday": "1990-01-15",
        "additional_info": "Friend from college"
      }

   **Errors**:
   
   * **422 Validation Error**: Invalid input data

Get Contact by ID
~~~~~~~~~~~~~~~~~

.. http:get:: /api/contacts/{contact_id}

   Retrieve a specific contact by ID.

   **Headers**: ``Authorization: Bearer <token>``

   **Parameters**:
   
   * ``contact_id`` (integer): Contact ID

   **Response** (200 OK):

   .. code-block:: json

      {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+1234567890", 
        "birthday": "1990-01-15",
        "additional_info": "Friend from college"
      }

   **Errors**:
   
   * **404 Not Found**: Contact not found or doesn't belong to user

Update Contact
~~~~~~~~~~~~~~

.. http:put:: /api/contacts/{contact_id}

   Update an existing contact.

   **Headers**:
   
   * ``Authorization: Bearer <token>``
   * ``Content-Type: application/json``

   **Parameters**:
   
   * ``contact_id`` (integer): Contact ID

   **Request Body** (all fields optional):

   .. code-block:: json

      {
        "first_name": "string",
        "last_name": "string",
        "email": "newemail@example.com", 
        "phone": "string",
        "birthday": "YYYY-MM-DD",
        "additional_info": "string"
      }

   **Response** (200 OK):

   .. code-block:: json

      {
        "id": 1,
        "first_name": "Updated Name",
        "last_name": "Doe",
        "email": "newemail@example.com",
        "phone": "+1234567890",
        "birthday": "1990-01-15", 
        "additional_info": "Updated info"
      }

   **Errors**:
   
   * **404 Not Found**: Contact not found or doesn't belong to user
   * **422 Validation Error**: Invalid input data

Delete Contact
~~~~~~~~~~~~~~

.. http:delete:: /api/contacts/{contact_id}

   Delete a contact.

   **Headers**: ``Authorization: Bearer <token>``

   **Parameters**:
   
   * ``contact_id`` (integer): Contact ID

   **Response** (204 No Content)

   **Errors**:
   
   * **404 Not Found**: Contact not found or doesn't belong to user

Search Contacts
~~~~~~~~~~~~~~~

.. http:get:: /api/contacts/search/{query}

   Search contacts by name, email, or phone.

   **Headers**: ``Authorization: Bearer <token>``

   **Parameters**:
   
   * ``query`` (string): Search term (minimum 3 characters)

   **Response** (200 OK):

   .. code-block:: json

      [
        {
          "id": 1,
          "first_name": "John",
          "last_name": "Doe",
          "email": "john@example.com", 
          "phone": "+1234567890",
          "birthday": "1990-01-15",
          "additional_info": "Friend from college"
        }
      ]

Upcoming Birthdays
~~~~~~~~~~~~~~~~~~

.. http:get:: /api/contacts/birthdays/upcoming

   Get contacts with birthdays in the next 7 days.

   **Headers**: ``Authorization: Bearer <token>``

   **Query Parameters**:
   
   * ``days`` (integer, optional): Number of days ahead to search. Default: 7

   **Response** (200 OK):

   .. code-block:: json

      [
        {
          "id": 1,
          "first_name": "John", 
          "last_name": "Doe",
          "email": "john@example.com",
          "phone": "+1234567890",
          "birthday": "1990-01-15",
          "additional_info": "Friend from college",
          "days_until_birthday": 3
        }
      ]

Data Validation
---------------

**Contact Fields**:

* ``first_name``: Required string, max 50 characters
* ``last_name``: Required string, max 50 characters  
* ``email``: Required valid email address, max 100 characters
* ``phone``: Required string, max 20 characters
* ``birthday``: Required date in YYYY-MM-DD format
* ``additional_info``: Optional text field

**Email Uniqueness**: 
Email addresses are not required to be unique across users - different users can have contacts with the same email address.

Security & Isolation
-------------------

**User Data Isolation**:
All contact operations are automatically filtered by the authenticated user's ID. Users cannot access or modify contacts belonging to other users.

**Authorization**:
All endpoints require a valid JWT token in the Authorization header. Requests without proper authentication return 401 Unauthorized.

**Input Validation**:
All input data is validated using Pydantic models. Invalid data returns 422 Unprocessable Entity with detailed validation errors.