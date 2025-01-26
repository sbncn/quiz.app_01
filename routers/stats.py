# routers/stats.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from tools.database import get_db
from tools.models import User, Statistics
from tools.token_generator import get_current_user

router = APIRouter()

class StatisticResponse(BaseModel):
    school_id: str
    class_name: str
    section_number: int
    correct_questions: int
    wrong_questions: int
    average_score: float
    section_percentage: float

@router.get("/", response_model=List[StatisticResponse], summary="View statistics")
def view_statistics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Only teachers or admins can view statistics.")

    if current_user.role == "admin":
        stats = db.query(Statistics).all()

    elif current_user.role == "teacher":
        if not current_user.registered_section:
            raise HTTPException(status_code=400, detail="Teacher has no registered section.")

        stats = db.query(Statistics).filter(
            Statistics.school_id == current_user.school_id,
            Statistics.class_name == current_user.class_name,
            # teacher’ın registered_section’ı “1” gibi bir string ise int() alabilirsiniz
            Statistics.section_number == int(current_user.registered_section)
        ).all()

    return [
        StatisticResponse(
            school_id=str(s.school_id),
            class_name=s.class_name,
            section_number=s.section_number,
            correct_questions=s.correct_questions,
            wrong_questions=s.wrong_questions,
            average_score=s.average_score,
            section_percentage=s.section_percentage
        )
        for s in stats
    ]
