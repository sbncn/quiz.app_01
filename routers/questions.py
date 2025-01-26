# routers/questions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from tools.database import get_db
from tools.models import User, Question, QuestionChoice
from tools.token_generator import get_current_user

router = APIRouter()

# ========= Pydantic Models =========
class ChoiceModel(BaseModel):
    choice_text: str
    is_correct: Optional[bool] = False
    correct_position: Optional[int] = None

class AddQuestionRequest(BaseModel):
    question_text: str
    q_type: str
    points: int
    # section zorunlu
    section: int
    # question şıkları (single, multiple, tf, ordering). 
    # Bir liste (her eleman bir ChoiceModel) bekleniyor
    choices: List[ChoiceModel] = []

class AddQuestionResponse(BaseModel):
    message: str
    external_id: str

class QuestionChoiceResponse(BaseModel):
    choice_text: str
    is_correct: bool
    correct_position: Optional[int]

class QuestionResponse(BaseModel):
    id: str
    external_id: str
    section: int
    question: str
    points: int
    q_type: str
    choices: List[QuestionChoiceResponse]

    class Config:
        orm_mode = True

# ========= Endpoints =========
@router.post("/", response_model=AddQuestionResponse, summary="Add a new question (advanced DB schema)")
def add_question(
    body: AddQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add questions.")

    external_id = str(uuid4())

    # Soru kaydet
    new_q = Question(
        external_id=external_id,
        section=body.section,
        question=body.question_text,
        points=body.points,
        type=body.q_type
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)

    # Soru şıkları kaydet
    for ch in body.choices:
        qc = QuestionChoice(
            question_id=new_q.id,
            choice_text=ch.choice_text.strip(),
            is_correct=ch.is_correct or False,
            correct_position=ch.correct_position
        )
        db.add(qc)
        db.commit()

    return {
        "message": "Question added successfully with new DB schema",
        "external_id": external_id
    }

@router.get("/", response_model=List[QuestionResponse], summary="List all questions (advanced DB schema)")
def list_all_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Only teachers or admins can list questions.")

    questions = db.query(Question).all()
    results = []
    for q in questions:
        choice_list = []
        for c in q.question_choices:
            choice_list.append(QuestionChoiceResponse(
                choice_text=c.choice_text,
                is_correct=c.is_correct,
                correct_position=c.correct_position
            ))
        results.append(QuestionResponse(
            id=str(q.id),
            external_id=q.external_id,
            section=q.section,
            question=q.question,
            points=q.points,
            q_type=q.type,
            choices=choice_list
        ))
    return results
