import asyncio
import threading
import ctypes
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.database import log_session, update_session_status
from app.automation.target import single_session_run

router = APIRouter(prefix="/automation", tags=["Automation"])

# Configuration from environment variables
MAX_THREADS = int(os.getenv("MAX_THREADS", "1"))

# Global variables for thread management
thread_pool = ThreadPoolExecutor()  # No max_workers limit
active_sessions: Dict[str, Dict] = {}  # session_id -> session_info
stop_flags: Dict[str, threading.Event] = {}  # session_id -> stop_event
session_lock = threading.Lock()

class StartRequest(BaseModel):
    search_keyword: str
    target_domain: str
    traffic_volume: int

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
async def start_automation(req: StartRequest):
    """Start automation session with specified traffic volume"""
    # Calculate optimal thread count based on traffic volume and MAX_THREADS
    thread_count = min(req.traffic_volume, MAX_THREADS)
    
    with session_lock:
        # Check if there are too many active sessions
        if len(active_sessions) >= MAX_THREADS:
            return {"status": "error", "message": f"Maximum number of active sessions ({MAX_THREADS}) reached."}
        
        # Validate traffic volume
        if req.traffic_volume < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Traffic volume must be at least 1"
            )
    
    # Log session start (without user)
    session_id = await log_session(
        "anonymous", req.search_keyword, req.target_domain, "started"
    )
    
    # Create stop flag for this session
    stop_flag = threading.Event()
    stop_flags[session_id] = stop_flag
    
    # Submit threads to thread pool
    futures = []
    for i in range(thread_count):
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
            'search_keyword': req.search_keyword,
            'target_domain': req.target_domain,
            'traffic_volume': req.traffic_volume,
            'thread_count': thread_count,
            'futures': futures,
            'stop_flag': stop_flag,
            'status': 'running'
        }
    
    return {
        "status": "started",
        "search_keyword": req.search_keyword,
        "target_domain": req.target_domain,
        "session_id": session_id,
        "traffic_volume": req.traffic_volume,
        "thread_count": thread_count,
        "message": f"Running {thread_count} threads for traffic volume of {req.traffic_volume}"
    }

@router.get("/status")
async def automation_status():
    """Get status of all automation sessions"""
    with session_lock:
        all_sessions = {
            session_id: {
                'search_keyword': session_info['search_keyword'],
                'target_domain': session_info['target_domain'],
                'traffic_volume': session_info['traffic_volume'],
                'thread_count': session_info['thread_count'],
                'status': session_info['status'],
                'running_threads': sum(1 for f in session_info['futures'] if not f.done())
            }
            for session_id, session_info in active_sessions.items()
        }
        
        # Calculate total threads
        total_threads = sum(len(s['futures']) for s in active_sessions.values())
        running_threads = sum(sum(1 for f in s['futures'] if not f.done()) for s in active_sessions.values())
        available_threads = total_threads - running_threads
    
    return {
        "active_sessions": all_sessions,
        "total_sessions": len(all_sessions),
        "total_threads": total_threads,
        "running_threads": running_threads,
        "available_threads": available_threads
    }

@router.get("/status/{session_id}")
async def get_session_status(session_id: str):
    """Get status of a specific session"""
    with session_lock:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session_info = active_sessions[session_id]
        running_threads = sum(1 for f in session_info['futures'] if not f.done())
        completed_threads = sum(1 for f in session_info['futures'] if f.done())
        
        return {
            "session_id": session_id,
            "search_keyword": session_info['search_keyword'],
            "target_domain": session_info['target_domain'],
            "traffic_volume": session_info['traffic_volume'],
            "thread_count": session_info['thread_count'],
            "running_threads": running_threads,
            "completed_threads": completed_threads,
            "status": session_info['status']
        }

@router.post("/stop")
async def stop_all_automation():
    """Stop all automation sessions"""
    session_ids = list(active_sessions.keys())
    
    if not session_ids:
        return {"status": "error", "message": "No active sessions found."}
    
    stopped_sessions = []
    for session_id in session_ids:
        result = await stop_session(session_id)
        stopped_sessions.append(result)
    
    return {
        "status": "stopped",
        "message": f"Stopped {len(stopped_sessions)} session(s)",
        "sessions": stopped_sessions
    }

@router.post("/stop/{session_id}")
async def stop_session(session_id: str):
    """Stop a specific automation session"""
    with session_lock:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Set stop flag
        stop_flag = stop_flags.get(session_id)
        if stop_flag:
            stop_flag.set()
        
        # Update session status
        active_sessions[session_id]['status'] = 'stopping'
    
    # Wait for threads to complete gracefully
    session_info = active_sessions[session_id]
    futures = session_info['futures']
    
    # Wait briefly for graceful shutdown
    completed = 0
    for future in futures:
        try:
            future.result(timeout=1.0)
            completed += 1
        except Exception:
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
        "total_threads": len(futures)
    }

@router.get("/config")
async def get_automation_config():
    """Get current automation configuration"""
    return {
        "max_threads": MAX_THREADS,
        "active_sessions": len(active_sessions),
        "total_running_threads": sum(len(s['futures']) for s in active_sessions.values()),
        "thread_pool_unlimited": True
    }