from fastapi import FastAPI
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import automation

app = FastAPI(title="TrafficFlux Session Runner", version="2.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_mongo_connection()

# Include routers
app.include_router(automation.router)

# Health check endpoint (no authentication required)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "TrafficFlux Session Runner is running"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "TrafficFlux Session Runner",
        "version": "2.0.0",
        "description": "Automated session runner",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)