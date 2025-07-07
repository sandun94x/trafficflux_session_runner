import os
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from app.auth import User, UserInDB, UserCreate, get_password_hash, verify_password

# MongoDB Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "trafficflux_db")

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(MONGO_URL)
        db.database = db.client[DATABASE_NAME]
        
        # Create indexes
        await db.database.users.create_index("username", unique=True)
        await db.database.users.create_index("email", unique=True)
        await db.database.sessions.create_index("user_id")
        await db.database.sessions.create_index("created_at")
        
        print(f"Connected to MongoDB: {DATABASE_NAME}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")

async def create_user(user_data: UserCreate) -> User:
    """Create a new user in the database"""
    try:
        # Check if user already exists
        existing_user = await db.database.users.find_one(
            {"$or": [{"username": user_data.username}, {"email": user_data.email}]}
        )
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Hash password and create user document
        hashed_password = get_password_hash(user_data.password)
        user_doc = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "disabled": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.database.users.insert_one(user_doc)
        
        # Return user without password
        return User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            disabled=False
        )
    except DuplicateKeyError:
        raise ValueError("Username or email already exists")
    except Exception as e:
        print(f"Error creating user: {e}")
        raise

async def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get user by username"""
    try:
        user_doc = await db.database.users.find_one({"username": username})
        if user_doc:
            return UserInDB(
                username=user_doc["username"],
                email=user_doc.get("email"),
                full_name=user_doc.get("full_name"),
                disabled=user_doc.get("disabled", False),
                hashed_password=user_doc["hashed_password"]
            )
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

async def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    try:
        user = await get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled
        )
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None

async def log_session(user_id: str, search_keyword: str, target_domain: str, status: str):
    """Log automation session to database"""
    try:
        session_doc = {
            "user_id": user_id,
            "search_keyword": search_keyword,
            "target_domain": target_domain,
            "status": status,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.database.sessions.insert_one(session_doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error logging session: {e}")
        return None

async def update_session_status(session_id: str, status: str):
    """Update session status"""
    try:
        from bson import ObjectId
        await db.database.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
    except Exception as e:
        print(f"Error updating session status: {e}")

async def get_user_sessions(username: str, limit: int = 10):
    """Get user's recent sessions"""
    try:
        sessions = await db.database.sessions.find(
            {"user_id": username},
            sort=[("created_at", -1)],
            limit=limit
        ).to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for session in sessions:
            session["_id"] = str(session["_id"])
        
        return sessions
    except Exception as e:
        print(f"Error getting user sessions: {e}")
        return []