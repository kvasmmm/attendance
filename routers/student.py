from fastapi import APIRouter, Depends, Request, HTTPException, Response
from datetime import datetime
import aiosqlite
from database import get_db
from schemas import StudentSubmit, StudentEdit
from logger import logger
from ws_manager import ws_manager

from config import ALLOWED_SUBNET, TRUSTED_IPS

router = APIRouter(prefix="/student", tags=["Student"])

@router.post("/submit")
async def submit_attendance(
    request: Request, 
    data: StudentSubmit, 
    response: Response, # <-- Инжектим Response, чтобы управлять куками
    db: aiosqlite.Connection = Depends(get_db)
):
    client_ip = request.client.host or "Unknown" # type: ignore
    user_agent = request.headers.get("user-agent", "Unknown")[:40]
    extra_data = {'clientip': client_ip, 'useragent': user_agent}

    is_trusted = client_ip in TRUSTED_IPS
    is_in_subnet = ALLOWED_SUBNET and client_ip.startswith(ALLOWED_SUBNET)
    
    if not (is_trusted or is_in_subnet):
        logger.warning(f"VPN/External network blocked: {client_ip} (Expected: {ALLOWED_SUBNET}*)", extra=extra_data)
        raise HTTPException(
            status_code=403, 
            detail=f"Network Error: Please connect to the local Wi-Fi ({ALLOWED_SUBNET}*)"
        )

    logger.info(f"Submit attempt: {data.student_id} with PIN {data.pin}", extra=extra_data)

    async with db.execute("SELECT id FROM sessions WHERE pin = ? AND is_active = 1", (data.pin,)) as cursor:
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(status_code=400, detail="Invalid PIN or session closed")
    
    session_id = session['id']

    device_cookie = request.cookies.get(f"attendance_{session_id}")
    if device_cookie and device_cookie != data.student_id:
        logger.warning(f"Cookie bypass attempt! Tried to submit {data.student_id}, but cookie says {device_cookie}", extra=extra_data)
        raise HTTPException(status_code=403, detail="Device block: This browser has already submitted attendance.")"

    async with db.execute("SELECT student_id FROM attendance WHERE session_id = ? AND ip_address = ?", (session_id, client_ip)) as cursor:
        existing = await cursor.fetchone()
        if existing:
            if existing['student_id'] == data.student_id:
                raise HTTPException(status_code=400, detail="Student ID already submitted.")
            else:
                raise HTTPException(status_code=403, detail="Device block: This IP has already submitted attendance.")

    # Сохраняем в БД
    now = datetime.now().isoformat()
    await db.execute("""
        INSERT INTO attendance (session_id, student_id, ip_address, created_at, updated_at, manual_entry)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (session_id, data.student_id, client_ip, now, now))
    await db.commit()

    await ws_manager.broadcast({
        "event": "new_student",
        "student_id": data.student_id,
        "timestamp": now,
        "ip": client_ip
    })

    response.set_cookie(
        key=f"attendance_{session_id}", 
        value=data.student_id, 
        max_age=43200,
        httponly=True 
    )

    logger.info(f"Success: {data.student_id} recorded", extra=extra_data)
    return {"status": "success", "session_id": session_id}


@router.put("/edit")
async def edit_attendance(
    request: Request, 
    data: StudentEdit, 
    db: aiosqlite.Connection = Depends(get_db)
):
    client_ip = request.client.host # type: ignore
    user_agent = request.headers.get("user-agent", "Unknown")[:40]
    extra_data = {'clientip': client_ip, 'useragent': user_agent}

    logger.info(f"Edit attempt: {data.old_student_id} -> {data.new_student_id}", extra=extra_data)
    
    async with db.execute("SELECT id FROM sessions WHERE pin = ? AND is_active = 1", (data.pin,)) as cursor:
        session = await cursor.fetchone()
        if not session:
            raise HTTPException(status_code=400, detail="Invalid PIN or session closed")
    session_id = session['id']

    if data.old_student_id != data.new_student_id:
        async with db.execute("SELECT id FROM attendance WHERE session_id = ? AND student_id = ?", (session_id, data.new_student_id)) as cursor:
            if await cursor.fetchone():
                raise HTTPException(status_code=400, detail="This Student ID is already submitted")

    now = datetime.now().isoformat()
    await db.execute("""
        UPDATE attendance SET student_id = ?, updated_at = ? 
        WHERE session_id = ? AND student_id = ?
    """, (data.new_student_id, now, session_id, data.old_student_id))
    await db.commit()

    await ws_manager.broadcast({
        "event": "edit_student",
        "old_student_id": data.old_student_id,
        "new_student_id": data.new_student_id,
        "timestamp": now,
        "ip": client_ip
    })

    logger.info(f"Edit success: {data.old_student_id} -> {data.new_student_id}", extra=extra_data)
    return {"status": "success"}

@router.get("/me")
async def get_my_info(request: Request):
    return {"ip": request.client.host}

