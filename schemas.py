from pydantic import BaseModel, Field
from typing import Optional

class SessionCreate(BaseModel):
    mode: str 

class StudentSubmit(BaseModel):
    # Field заставит FastAPI автоматически выкидывать 422 ошибку, если формат не совпадет
    student_id: str = Field(..., pattern=r"^202\d{6}$")
    pin: str 

class StudentEdit(BaseModel):
    old_student_id: str
    new_student_id: str = Field(..., pattern=r"^202\d{6}$")
    pin: str

class ManualEntry(BaseModel):
    student_id: str = Field(..., pattern=r"^202\d{6}$")
    session_id: str

# Если создал схему для препода:
class ProfEditStudent(BaseModel):
    old_student_id: str
    new_student_id: str = Field(..., pattern=r"^202\d{6}$")
    
class ProfAddStudent(BaseModel):
    student_id: str = Field(..., pattern=r"^202\d{6}$")