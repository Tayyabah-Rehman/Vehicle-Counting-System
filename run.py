import uvicorn

if __name__ == "__main__":
    print("Starting Vehicle Counting System API Server")
    print("GPU Available: Check /api/health endpoint")
    print("API Documentation: http://localhost:8000/docs")
    print("WebSocket endpoint: ws://localhost:8000/ws/{job_id}")
    print("Press Ctrl+C to stop the server")

    uvicorn.run(
        "backend.app.api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )