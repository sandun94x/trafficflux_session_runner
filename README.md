# TrafficFlux Session Runner with JWT Authentication and Multithreading

A FastAPI-based automation session runner with JWT authentication, MongoDB integration, and multithreading support for concurrent automation sessions.

## Features

- **JWT Authentication**: Secure token-based authentication system
- **User Management**: Register, login, and manage user accounts
- **MongoDB Integration**: Store user credentials and session logs
- **Session Tracking**: Track automation sessions per user
- **Protected Endpoints**: All automation endpoints require authentication
- **Multithreading Support**: Run multiple concurrent automation sessions
- **Configurable Thread Pool**: Environment-based thread pool configuration

## Setup and Installation

### Prerequisites

- Python 3.8+
- MongoDB (local or cloud instance)
- Required Python packages (see requirements.txt)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up MongoDB:
   - Install MongoDB locally or use MongoDB Atlas
   - Update the `MONGO_URL` environment variable if needed

3. Set environment variables:
```bash
# Optional: Set custom MongoDB URL
export MONGO_URL="mongodb://localhost:27017"

# Optional: Set custom database name
export DATABASE_NAME="trafficflux_db"

# Important: Set a secure secret key for JWT tokens
export SECRET_KEY="your-very-secure-secret-key-here"

# Threading Configuration
export MAX_THREADS="4"           # Maximum threads per user session
export THREAD_POOL_SIZE="10"     # Total thread pool size
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123",
    "full_name": "Test User"
}
```

**Response:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "disabled": false
}
```

#### POST /auth/login
Login and receive JWT access token.

**Request Body:**
```json
{
    "username": "testuser",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

#### GET /auth/me
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "disabled": false
}
```

#### GET /auth/my-sessions
Get current user's session history (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

### Automation Endpoints (Protected)

All automation endpoints require JWT authentication via the `Authorization: Bearer <token>` header.

#### POST /automation/start
Start a single automation session.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "search_keyword": "precision mechanical keyboard-kb1001",
    "target_domain": "https://test.verdic.ai/products/keyboard.html"
}
```

**Response:**
```json
{
    "status": "started",
    "search_keyword": "precision mechanical keyboard-kb1001",
    "target_domain": "https://test.verdic.ai/products/keyboard.html",
    "session_id": "60f7b5c4d1e2f3a4b5c6d7e8",
    "thread_count": 1,
    "user": "testuser"
}
```

#### POST /automation/start-multi
Start multiple automation sessions with specified thread count.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
    "search_keyword": "precision mechanical keyboard-kb1001",
    "target_domain": "https://test.verdic.ai/products/keyboard.html",
    "thread_count": 3
}
```

**Response:**
```json
{
    "status": "started",
    "search_keyword": "precision mechanical keyboard-kb1001",
    "target_domain": "https://test.verdic.ai/products/keyboard.html",
    "session_id": "60f7b5c4d1e2f3a4b5c6d7e8",
    "thread_count": 3,
    "user": "testuser"
}
```

#### GET /automation/status
Get status of all automation sessions for current user.

**Response:**
```json
{
    "user": "testuser",
    "active_sessions": {
        "60f7b5c4d1e2f3a4b5c6d7e8": {
            "search_keyword": "precision mechanical keyboard-kb1001",
            "target_domain": "https://test.verdic.ai/products/keyboard.html",
            "thread_count": 3,
            "status": "running",
            "running_threads": 2
        }
    },
    "total_sessions": 1
}
```

#### GET /automation/status/{session_id}
Get status of a specific automation session.

**Response:**
```json
{
    "session_id": "60f7b5c4d1e2f3a4b5c6d7e8",
    "search_keyword": "precision mechanical keyboard-kb1001",
    "target_domain": "https://test.verdic.ai/products/keyboard.html",
    "total_threads": 3,
    "running_threads": 2,
    "completed_threads": 1,
    "status": "running"
}
```

#### POST /automation/stop
Stop all automation sessions for current user.

#### POST /automation/stop/{session_id}
Stop a specific automation session.

#### GET /automation/config
Get current automation configuration.

**Response:**
```json
{
    "max_threads": 4,
    "thread_pool_size": 10,
    "active_sessions": 1,
    "available_threads": 7
}
```

### Public Endpoints

#### GET /health
Health check endpoint (no authentication required).

#### GET /
Root endpoint with API information.

## Multithreading Configuration

The application supports configurable multithreading through environment variables:

- **MAX_THREADS**: Maximum number of threads per user session (default: 4)
- **THREAD_POOL_SIZE**: Total size of the thread pool (default: 10)

### Thread Management

- Each user can run multiple automation sessions concurrently
- Each session can have multiple threads (up to MAX_THREADS)
- Thread pool prevents system overload
- Graceful shutdown of threads when sessions are stopped
- Real-time thread status monitoring

### Example Usage

1. **Single Thread Session:**
```bash
POST /automation/start
{
    "search_keyword": "example keyword",
    "target_domain": "https://example.com"
}
```

2. **Multi-Thread Session:**
```bash
POST /automation/start-multi
{
    "search_keyword": "example keyword",
    "target_domain": "https://example.com",
    "thread_count": 3
}
```

3. **Monitor Thread Status:**
```bash
GET /automation/status
```

4. **Stop Specific Session:**
```bash
POST /automation/stop/60f7b5c4d1e2f3a4b5c6d7e8
```

## Database Schema

### Users Collection
```json
{
    "_id": ObjectId,
    "username": "string",
    "email": "string",
    "full_name": "string",
    "hashed_password": "string",
    "disabled": boolean,
    "created_at": DateTime,
    "updated_at": DateTime
}
```

### Sessions Collection
```json
{
    "_id": ObjectId,
    "user_id": "string",
    "search_keyword": "string",
    "target_domain": "string",
    "status": "string",
    "created_at": DateTime,
    "updated_at": DateTime
}
```

## Usage with Postman

1. Import the provided Postman collection: `TrafficFlux_API.postman_collection.json`
2. Register a new user using the `/auth/register` endpoint
3. Login using the `/auth/login` endpoint - the collection will automatically save the JWT token
4. Use the protected endpoints with automatic Bearer token authentication
5. Test multithreading with the `/automation/start-multi` endpoint

## Security Features

- **Password Hashing**: Uses bcrypt for secure password storage
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Token Verification**: All protected endpoints verify JWT tokens
- **MongoDB Indexes**: Unique constraints on username and email
- **Environment Variables**: Secure configuration via environment variables
- **Thread Isolation**: Each user's sessions are isolated from others

## Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Multithreading
1. Use the Postman collection for comprehensive API testing
2. Test single and multi-threaded sessions
3. Monitor thread status and performance
4. Test graceful shutdown of threads

## Production Considerations

1. **Set a Strong Secret Key**: Use a cryptographically secure random string
2. **Use HTTPS**: Always use HTTPS in production
3. **MongoDB Security**: Secure your MongoDB instance with authentication
4. **Token Expiration**: Configure appropriate token expiration times
5. **Rate Limiting**: Consider implementing rate limiting for API endpoints
6. **Thread Pool Sizing**: Adjust thread pool size based on server resources
7. **Resource Monitoring**: Monitor CPU and memory usage with multiple threads

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | MongoDB database name | `trafficflux_db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here-change-in-production` |
| `MAX_THREADS` | Maximum threads per user session | `4` |
| `THREAD_POOL_SIZE` | Total thread pool size | `10` |

## Thread Pool Architecture

```
ThreadPoolExecutor
├── Thread Pool Size: 10 (configurable)
├── Max Threads per User: 4 (configurable)
├── Session Management: Per-user isolation
├── Graceful Shutdown: Stop flags for clean termination
└── Status Monitoring: Real-time thread status tracking
```

## License

This project is proprietary software.