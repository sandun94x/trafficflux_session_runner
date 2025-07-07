from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from app.auth import Token, User, UserCreate, UserLogin, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import create_user, authenticate_user, get_user_sessions
from app.dependencies import get_current_active_user
from fastapi import Depends

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login_user(user_data: UserLogin):
    """Login user and return JWT token"""
    user = await authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@router.get("/my-sessions")
async def get_my_sessions(current_user: User = Depends(get_current_active_user)):
    """Get current user's session history"""
    sessions = await get_user_sessions(current_user.username)
    return {"sessions": sessions}