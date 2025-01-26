from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from tools.database import get_db
from tools.models import User, Exam, ExamAnswer, Question, QuestionChoice
from tools.token_generator import get_current_user

router = APIRouter()

class AnswerDetail(BaseModel):
    question_id: str
    external_id: str
    question: str
    user_answer: str
    is_correct: bool
    points_earned: int

class ExamDetail(BaseModel):
    exam_id: str
    start_time: str
    end_time: str | None
    score_avg: float
    answers: List[AnswerDetail]

class ExamResultResponse(BaseModel):
    exams: List[ExamDetail]

@router.get("/results", response_model=ExamResultResponse, summary="View your exam results")
def view_exam_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view their exam results.")

    exams = db.query(Exam).filter(Exam.user_id == current_user.user_id).all()
    if not exams:
        return {"exams": []}

    exam_details = []
    for exam in exams:
        exam_answers = db.query(ExamAnswer).filter(ExamAnswer.exam_id == exam.exam_id).all()
        answers_out = []

        for ans in exam_answers:
            # Soru tablosundan asıl soruyu bul
            question_obj = db.query(Question).filter(Question.id == ans.question_id).first()
            if not question_obj:
                continue

            # Kullanıcının işaretlediği choice_text'leri al
            user_choices = ans.user_choices  # birden çok olabilir
            chosen_texts = []
            for uc in user_choices:
                qc = db.query(QuestionChoice).filter(QuestionChoice.id == uc.question_choice_id).first()
                if qc:
                    chosen_texts.append(qc.choice_text)

            # 'is_correct' hesaplayalım. Basitçe 'kazandığı puan == soru puanı' kontrolü
            # (Tabii bu her soru tipi için "tam puan = doğru" mantığına dayanıyor)
            is_correct = (ans.points_earned == question_obj.points)

            answers_out.append(AnswerDetail(
                question_id=str(question_obj.id),
                external_id=question_obj.external_id,
                question=question_obj.question,
                user_answer=", ".join(chosen_texts),
                is_correct=is_correct,
                points_earned=ans.points_earned
            ))

        exam_details.append(ExamDetail(
            exam_id=str(exam.exam_id),
            start_time=exam.start_time.isoformat(),
            end_time=exam.end_time.isoformat() if exam.end_time else None,
            score_avg=current_user.score_avg,
            answers=answers_out
        ))

    return {"exams": exam_details}
