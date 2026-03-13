import uuid
import random
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.responses import PlainTextResponse
from datetime import datetime
import aiosqlite
from database import get_db
from schemas import SessionCreate, ProfAddStudent
from logger import logger
from ws_manager import ws_manager
import utils_export
from pydantic import BaseModel

class ProfEditStudent(BaseModel):
    old_student_id: str
    new_student_id: str
    
    
router = APIRouter(prefix="/professor", tags=["Professor"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@router.post("/session/start")
async def start_session(data: SessionCreate, db: aiosqlite.Connection = Depends(get_db)):
    session_id = str(uuid.uuid4())
    pin = str(random.randint(100000, 999999))
    now = datetime.now().isoformat()
    
    await db.execute("""
        INSERT INTO sessions (id, mode, pin, start_time, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (session_id, data.mode, pin, now))
    await db.commit()
    
    logger.info(f"Session started: {session_id} | PIN: {pin}")
    return {"session_id": session_id, "pin": pin}

@router.post("/session/{session_id}/close")
async def close_session(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    now = datetime.now().isoformat()
    await db.execute("UPDATE sessions SET is_active = 0, end_time = ? WHERE id = ?", (now, session_id))
    await db.commit()
    logger.info(f"Session closed: {session_id}")
    return {"status": "closed"}
@router.post("/session/{session_id}/student/manual")
async def add_student_manual(session_id: str, data: ProfAddStudent, db: aiosqlite.Connection = Depends(get_db)):
    now = datetime.now().isoformat()
    
    async with db.execute("SELECT id FROM attendance WHERE session_id = ? AND student_id = ?", (session_id, data.student_id)) as cursor:
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Student already exists in this session.")
    
    await db.execute("""
        INSERT INTO attendance (session_id, student_id, ip_address, created_at, updated_at, manual_entry)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (session_id, data.student_id, "Prof Manual", now, now))
    await db.commit()
    
    logger.info(f"Prof manually added student {data.student_id}", extra={'clientip': 'PROF', 'useragent': 'Host'})
    
    await ws_manager.broadcast({
        "event": "new_student",
        "student_id": data.student_id,
        "timestamp": now,
        "ip": "Prof Manual",
        "manual_entry": True
    })
    return {"status": "added"}
@router.get("/session/active")
async def get_active_session(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT id, pin FROM sessions WHERE is_active = 1 ORDER BY start_time DESC LIMIT 1") as cursor:
        session = await cursor.fetchone()
        
    if not session:
        return {"active": False}
        
    session_id = session['id']
    
    async with db.execute("SELECT student_id, ip_address, created_at, manual_entry FROM attendance WHERE session_id = ? ORDER BY created_at ASC", (session_id,)) as cursor:
        rows = await cursor.fetchall()
        
    students = [{
        "student_id": row["student_id"],
        "ip": row["ip_address"],
        "timestamp": row["created_at"],
        "manual_entry": bool(row["manual_entry"])
    } for row in rows]
    
    return {
        "active": True,
        "session_id": session_id,
        "pin": session['pin'],
        "students": students
    }

import csv
from io import StringIO
from fastapi.responses import Response

@router.get("/export/{session_id}/csv")
async def export_attendance_csv(session_id: str, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT student_id, ip_address, created_at, manual_entry FROM attendance WHERE session_id = ?", (session_id,)) as cursor:
        rows = await cursor.fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Timestamp", "IP Address", "Manual Entry"])
    
    for row in rows:
        writer.writerow([row['student_id'], row['created_at'], row['ip_address'], "Yes" if row['manual_entry'] else "No"])

    csv_data = output.getvalue().encode('utf-8')
    
    return Response(
        content=csv_data, 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename=attendance_{session_id}.csv"}
    )
    
@router.delete("/session/{session_id}/student/{student_id}")
async def delete_student(session_id: str, student_id: str, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM attendance WHERE session_id = ? AND student_id = ?", (session_id, student_id))
    await db.commit()
    
    logger.info(f"Prof deleted student {student_id} from session {session_id}", extra={'clientip': 'PROF', 'useragent': 'Host'})
    await ws_manager.broadcast({"event": "delete_student", "student_id": student_id})
    return {"status": "deleted"}

@router.put("/session/{session_id}/student")
async def edit_student_prof(session_id: str, data: ProfEditStudent, db: aiosqlite.Connection = Depends(get_db)):
    now = datetime.now().isoformat()
    await db.execute("UPDATE attendance SET student_id = ?, updated_at = ? WHERE session_id = ? AND student_id = ?", 
                     (data.new_student_id, now, session_id, data.old_student_id))
    await db.commit()
    
    logger.info(f"Prof edited student {data.old_student_id} -> {data.new_student_id}", extra={'clientip': 'PROF', 'useragent': 'Host'})
    await ws_manager.broadcast({
        "event": "edit_student",
        "old_student_id": data.old_student_id,
        "new_student_id": data.new_student_id,
        "timestamp": now,
        "ip": "Prof manual edit"
    })
    return {"status": "edited"}