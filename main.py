import webbrowser
import threading
import time
import socket
import secrets
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import aiosqlite
from database import init_db
from logger import logger
from routers import student, professor

from config import HOST_IP

app = FastAPI(title="Local Attendance Host")

PROF_TOKEN = secrets.token_urlsafe(16)
logger.info(f"Professor token generated: {PROF_TOKEN}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def open_browser():
    time.sleep(1.5)
    url = f"http://{HOST_IP}:8000/{PROF_TOKEN}"
    webbrowser.open(url)
    logger.info(f"Professor dashboard opened: {url}")
    
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up server...")
    await init_db()
    async with aiosqlite.connect("attendance.db") as db: 
        await db.execute("UPDATE sessions SET is_active = 0 WHERE is_active = 1")
        await db.commit()
        logger.info("All sessions reset at startup")

    threading.Thread(target=open_browser, daemon=True).start()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    
    extra_data = {'clientip': client_ip, 'useragent': user_agent}
    
    logger.debug(f"HTTP Request: {request.method} {request.url.path}", extra=extra_data)
    response = await call_next(request)
    logger.debug(f"HTTP Response: {response.status_code}", extra=extra_data)
    return response

app.include_router(student.router)
app.include_router(professor.router)

@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/student.html")

@app.get(f"/{PROF_TOKEN}")
async def get_prof_dashboard():
    return FileResponse("professor.html")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)