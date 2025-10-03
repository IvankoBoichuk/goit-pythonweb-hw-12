# GoIT Python Web HW-12

FastAPI contacts management application with PostgreSQL database and JWT Authentication.

## Features

- User registration and authentication
- JWT token-based security
- Protected contact management endpoints
- User-specific data isolation

## Setup

1. Copy environment configuration:
```bash
cp .env.example .env
```

2. Update the `.env` file with your configuration (especially the SECRET_KEY)

3. Build and run with Docker:
```bash
docker compose up --build
```

4. The API will be available at http://localhost:8000

## Authentication

The application uses JWT (JSON Web Tokens) for authentication. All contact endpoints require authentication.

### Endpoints

#### Authentication:
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get access token
- `GET /api/auth/me` - Get current user info

#### Avatar Management:
- `POST /api/auth/avatar` - Upload user avatar (multipart/form-data)
- `DELETE /api/auth/avatar` - Delete user avatar

#### Contacts (Protected):
- `GET /api/contacts` - Get all contacts
- `POST /api/contacts` - Create a new contact
- `GET /api/contacts/{id}` - Get contact by ID
- `PUT /api/contacts/{id}` - Update contact
- `DELETE /api/contacts/{id}` - Delete contact
- `GET /api/contacts/search/{query}` - Search contacts
- `GET /api/contacts/birthdays/upcoming` - Get upcoming birthdays

### Usage Example

1. Register a user:
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

2. Login to get access token:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

3. Use the token to access protected endpoints:
```bash
curl -X GET "http://localhost:8000/api/contacts" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

- `SECRET_KEY`: JWT secret key (change in production!)
- `DATABASE_URL`: PostgreSQL connection string
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)
- `DEBUG`: Debug mode (default: False)