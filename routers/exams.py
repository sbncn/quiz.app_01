# routers/exams.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
from uuid import UUID
from tools.database import get_db
from tools.models import User, Exam, Question, exam_question_association
from tools.exam import select_questions, process_results
from tools.token_generator import get_current_user

router = APIRouter()

class ChoiceAnswer(BaseModel):
    # "choice_text" (tekil) veya "ordered_list" (ordering için)
    # Burada basit bir örnek: multiple ise list[str], single/tf => tek str
    selected_texts: Optional[List[str]] = None
    # ordering tipinde mesela kullanıcı "1,2,3,4" gibi
    # bu örnekte tek bir list'e koyabiliriz.

class SubmitExamRequest(BaseModel):
    exam_id: UUID
    # "answers": { "question_id": ChoiceAnswer }
    answers: Dict[str, ChoiceAnswer]

class SubmitExamResponse(BaseModel):
    message: str

@router.post("/start", summary="Start an exam")
def start_exam_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can start an exam.")
    if current_user.attempts >= 2:
        raise HTTPException(status_code=400, detail="You have no remaining exam attempts.")

    selected_questions = select_questions(db, current_user)
    if not selected_questions:
        raise HTTPException(status_code=400, detail="No questions available.")

    # Create Exam
    exam = Exam(
        user_id=current_user.user_id,
        class_name=current_user.class_name,
        school_id=current_user.school_id,
        start_time=datetime.utcnow()
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    # Associate selected questions
    all_selected = []
    for qs in selected_questions.values():
        all_selected.extend(qs)
    exam.selected_questions = all_selected
    db.commit()

    # Geri dönerken, her question'ın question_choices’larını da verelim:
    # (UI tarafta “Şıklar”'ı gösterebilmek için.)
    response_questions = {}
    for sec, qs in selected_questions.items():
        qlist = []
        for q in qs:
            # question_choices tablosundan verileri
            qc_list = []
            for choice_row in q.question_choices:
                qc_list.append({
                    "choice_id": str(choice_row.id),
                    "choice_text": choice_row.choice_text
                })
            qlist.append({
                "question_id": str(q.id),
                "external_id": q.external_id,
                "question": q.question,
                "points": q.points,
                "type": q.type,
                "choices": qc_list
            })
        response_questions[sec] = qlist

    return {
        "message": "Exam started",
        "exam_id": exam.exam_id,
        "questions": response_questions
    }


@router.post("/submit", response_model=SubmitExamResponse, summary="Submit exam answers")
def submit_exam_endpoint(
    body: SubmitExamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can submit exam answers.")
    if current_user.attempts >= 2:
        raise HTTPException(status_code=400, detail="You have no remaining exam attempts.")

    exam = db.query(Exam).filter(Exam.exam_id == body.exam_id, Exam.user_id == current_user.user_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found.")
    if exam.end_time is not None:
        raise HTTPException(status_code=400, detail="Exam has already been submitted.")

    # selected_questions
    def get_selected_questions_for_exam(db: Session, exam: Exam):
        selected_qs = db.query(Question).join(exam_question_association).filter(
            exam_question_association.c.exam_id == exam.exam_id
        ).all()
        return selected_qs

    selected_qs = get_selected_questions_for_exam(db, exam)
    if not selected_qs:
        raise HTTPException(status_code=400, detail="No questions associated with this exam.")

    end_time = datetime.utcnow()
    process_results(db, current_user, exam, selected_qs, body.answers, end_time)
    return {"message": "Exam submitted successfully."}
