import asyncio
import threading
import ctypes
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.auth import User
from app.dependencies import get_current_active_user
from app.database import log_session, update_session_status
from app.automation.target import single_session_run

router = APIRouter(prefix="/automation", tags=["Automation"])

# Configuration from environment variables
MAX_THREADS = int(os.getenv("MAX_THREADS", "4"))
THREAD_POOL_SIZE = int(os.getenv("THREAD_POOL_SIZE", "10"))

# Global variables for thread management
thread_pool = ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE)
active_sessions: Dict[str, Dict] = {}  # session_id -> session_info
stop_flags: Dict[str, threading.Event] = {}  # session_id -> stop_event
session_lock = threading.Lock()

class StartRequest(BaseModel):
    search_keyword: str
    target_domain: str

class MultiThreadRequest(BaseModel):
    search_keyword: str
    target_domain: str
    thread_count: int = 1

def run_automation_worker(search_keyword: str, target_domain: str, stop_flag: threading.Event, session_id: str, thread_id: int):
    """Worker function for individual automation threads"""
    try:
        print(f"[Thread {thread_id}] Starting automation for session {session_id}")
        asyncio.run(single_session_run(search_keyword, target_domain, stop_flag))
        print(f"[Thread {thread_id}] Completed automation for session {session_id}")
    except Exception as e:
        print(f"[Thread {thread_id}] Error in automation: {e}")

def force_terminate_thread(thread):
    """Force terminate a thread (use with caution)"""
    if not thread.is_alive():
        return
    
    thread_id = thread.ident
    if thread_id is None:
        return
    
    try:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), 
            ctypes.py_object(SystemExit)
        )
    except Exception as e:
        print(f"Failed to force terminate thread: {e}")

@router.post("/start")
async def start_automation(req: StartRequest, current_user: User = Depends(get_current_active_user)):
    """Start a single automation session"""
    return await start_multi_automation(
        MultiThreadRequest(
            search_keyword=req.search_keyword,
            target_domain=req.target_domain,
            thread_count=1
        ),
        current_user
    )

@router.post("/start-multi")
async def start_multi_automation(req: MultiThreadRequest, current_user: User = Depends(get_current_active_user)):
    """Start multiple automation sessions with specified thread count"""
    with session_lock:
        # Check if user already has running sessions
        user_sessions = [s for s in active_sessions.values() if s['user'] == current_user.username]
        if user_sessions:
            return {"status": "error", "message": f"User already has {len(user_sessions)} active session(s)."}
        
        # Validate thread count
        if req.thread_count > MAX_THREADS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Thread count cannot exceed {MAX_THREADS}"
            )
        
        if req.thread_count < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thread count must be at least 1"
            )
    
    # Log session start
    session_id = await log_session(
        current_user.username, req.search_keyword, req.target_domain, "started"
    )
    
    # Create stop flag for this session
    stop_flag = threading.Event()
    stop_flags[session_id] = stop_flag
    
    # Submit threads to thread pool
    futures = []
    for i in range(req.thread_count):
        future = thread_pool.submit(
            run_automation_worker,
            req.search_keyword,
            req.target_domain,
            stop_flag,
            session_id,
            i + 1
        )
        futures.append(future)
    
    # Store session info
    with session_lock:
        active_sessions[session_id] = {
            'user': current_user.username,
            'search_keyword': req.search_keyword,
            'target_domain': req.target_domain,
            'thread_count': req.thread_count,
            'futures': futures,
            'stop_flag': stop_flag,
            'status': 'running'
        }
    
    return {
        "status": "started",
        "search_keyword": req.search_keyword,
        "target_domain": req.target_domain,
        "session_id": session_id,
        "thread_count": req.thread_count,
        "user": current_user.username
    }

@router.get("/status")
async def automation_status(current_user: User = Depends(get_current_active_user)):
    """Get status of all automation sessions for current user"""
    with session_lock:
        user_sessions = {
            session_id: {
                'search_keyword': session_info['search_keyword'],
                'target_domain': session_info['target_domain'],
                'thread_count': session_info['thread_count'],
                'status': session_info['status'],
                'running_threads': sum(1 for f in session_info['futures'] if not f.done())
            }
            for session_id, session_info in active_sessions.items()
            if session_info['user'] == current_user.username
        }
    
    return {
        "user": current_user.username,
        "active_sessions": user_sessions,
        "total_sessions": len(user_sessions)
    }

@router.get("/status/{session_id}")
async def get_session_status(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Get status of a specific session"""
    with session_lock:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session_info = active_sessions[session_id]
        if session_info['user'] != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        running_threads = sum(1 for f in session_info['futures'] if not f.done())
        completed_threads = sum(1 for f in session_info['futures'] if f.done())
        
        return {
            "session_id": session_id,
            "search_keyword": session_info['search_keyword'],
            "target_domain": session_info['target_domain'],
            "total_threads": session_info['thread_count'],
            "running_threads": running_threads,
            "completed_threads": completed_threads,
            "status": session_info['status']
        }

@router.post("/stop")
async def stop_all_automation(current_user: User = Depends(get_current_active_user)):
    """Stop all automation sessions for current user"""
    with session_lock:
        user_sessions = [
            session_id for session_id, session_info in active_sessions.items()
            if session_info['user'] == current_user.username
        ]
    
    if not user_sessions:
        return {"status": "error", "message": "No active sessions found for user."}
    
    stopped_sessions = []
    for session_id in user_sessions:
        result = await stop_session(session_id, current_user)
        stopped_sessions.append(result)
    
    return {
        "status": "stopped",
        "message": f"Stopped {len(stopped_sessions)} session(s)",
        "sessions": stopped_sessions,
        "user": current_user.username
    }

@router.post("/stop/{session_id}")
async def stop_session(session_id: str, current_user: User = Depends(get_current_active_user)):
    """Stop a specific automation session"""
    with session_lock:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session_info = active_sessions[session_id]
        if session_info['user'] != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Set stop flag
        stop_flag = stop_flags.get(session_id)
        if stop_flag:
            stop_flag.set()
        
        # Update session status
        session_info['status'] = 'stopping'
    
    # Wait for threads to complete gracefully
    session_info = active_sessions[session_id]
    futures = session_info['futures']
    
    # Wait briefly for graceful shutdown
    completed = 0
    for future in futures:
        try:
            future.result(timeout=1.0)
            completed += 1
        except:
            pass
    
    # Clean up
    with session_lock:
        if session_id in active_sessions:
            del active_sessions[session_id]
        if session_id in stop_flags:
            del stop_flags[session_id]
    
    # Update session status in database
    await update_session_status(session_id, "stopped")
    
    return {
        "status": "stopped",
        "session_id": session_id,
        "threads_completed": completed,
        "total_threads": len(futures),
        "user": current_user.username
    }

@router.get("/config")
async def get_automation_config(current_user: User = Depends(get_current_active_user)):
    """Get current automation configuration"""
    return {
        "max_threads": MAX_THREADS,
        "thread_pool_size": THREAD_POOL_SIZE,
        "active_sessions": len(active_sessions),
        "available_threads": THREAD_POOL_SIZE - sum(len(s['futures']) for s in active_sessions.values())
    }