# tools/exam.py
import random
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, List
from tools.models import Question, QuestionChoice, Exam, ExamAnswer, UserChoice, User
from tools.statistics_utils import update_statistics

def load_questions(db: Session):
    return db.query(Question).all()

def select_questions(db: Session, user: User):
    if user.attempts >= 2:
        return None
    questions = load_questions(db)

    # basit random logic -> her section'dan 5 tane
    sections = {1: [], 2: [], 3: [], 4: []}
    for sec in range(1, 5):
        sec_qs = [q for q in questions if q.section == sec]
        selected = sec_qs if len(sec_qs) < 5 else random.sample(sec_qs, 5)
        sections[sec] = selected
    return sections

def process_results(db: Session, user: User, exam: Exam, selected_questions: List[Question], answers_dict, end_time):
    # "answers_dict" => { question_id: { "selected_texts": [..] } }

    section_correct = {1: 0, 2: 0, 3: 0, 4: 0}
    section_wrong = {1: 0, 2: 0, 3: 0, 4: 0}
    section_scores = {1: 0, 2: 0, 3: 0, 4: 0}

    for q in selected_questions:
        ans_data = answers_dict.get(str(q.id))
        if not ans_data:
            # User hiç cevap vermemiş
            create_exam_answer(db, exam, q, 0, [])  # 0 puan
            section_wrong[q.section] += 1
            continue

        selected_texts = ans_data.selected_texts or []
        # "selected_texts" -> list[str], ordering / multiple / single / tf

        # 1) ExamAnswer kaydı
        exam_ans = create_exam_answer(db, exam, q, 0, selected_texts)

        # 2) Doğruluk kontrolü
        points_earned, is_correct = evaluate_question(db, q, selected_texts)
        exam_ans.points_earned = points_earned
        db.commit()

        if is_correct:
            section_correct[q.section] += 1
            section_scores[q.section] += points_earned
        else:
            section_wrong[q.section] += 1

    # Kullanıcının attempt/panel vs.
    user.attempts += 1
    user.last_attempt_date = datetime.now()
    total_score = sum(section_scores.values())
    general_percentage = (total_score / 20) * 100 if total_score > 0 else 0  # 20 puan = rastgele max?

    if user.attempts == 1:
        user.score1 = general_percentage
        user.score_avg = general_percentage
    elif user.attempts == 2:
        user.score2 = general_percentage
        user.score_avg = (user.score1 + user.score2) / 2

    exam.end_time = end_time
    db.commit()

    # İstatistik
    update_statistics(db, user.school_id, user.class_name, section_correct, section_wrong, section_scores)


def create_exam_answer(db: Session, exam: Exam, question: Question, points_earned: int, selected_texts: List[str]):
    exam_ans = ExamAnswer(
        exam_id=exam.exam_id,
        question_id=question.id,
        points_earned=points_earned
    )
    db.add(exam_ans)
    db.commit()
    db.refresh(exam_ans)

    # Tüm seçenekleri bir kere çek
    all_choices = db.query(QuestionChoice).filter(QuestionChoice.question_id == question.id).all()
    
    if question.type == "ordering":
        if len(selected_texts) == 1 and "," in selected_texts[0]:
            splitted = [x.strip() for x in selected_texts[0].split(",")]
        else:
            splitted = selected_texts

        for idx, val in enumerate(splitted):
            normalized_val = val.strip().lower()
            # Tüm seçeneklerde normalize ederek ara
            for choice in all_choices:
                if choice.choice_text.strip().lower() == normalized_val:
                    uc = UserChoice(
                        exam_answer_id=exam_ans.id,
                        question_choice_id=choice.id,
                        user_position=idx
                    )
                    db.add(uc)
                    db.commit()
                    break

    elif question.type in ["single_choice", "multiple_choice", "true_false"]:
        for txt in selected_texts:
            normalized_txt = txt.strip().lower()
            # Tüm seçeneklerde normalize ederek ara
            for choice in all_choices:
                if choice.choice_text.strip().lower() == normalized_txt:
                    uc = UserChoice(
                        exam_answer_id=exam_ans.id,
                        question_choice_id=choice.id
                    )
                    db.add(uc)
                    db.commit()
                    break
    
    return exam_ans


def evaluate_question(db: Session, question: Question, selected_texts: List[str]):
    """
    Sorunun tipine göre user'ın seçimini doğru/yanlış değerlendirip puan döndürüyoruz.
    """
    # max alabileceği puan = question.points
    # Bu basit örnekte, "tam doğruysa full puan, aksi 0" diyelim.

    if question.type == "true_false":
        # Tek bir choice doğru, user da tek bir choice seçmişse -> check
        correct_choice = db.query(QuestionChoice).filter_by(question_id=question.id, is_correct=True).first()
        if not correct_choice:
            return (0, False)
        if len(selected_texts) == 1 and selected_texts[0] == correct_choice.choice_text:
            return (question.points, True)
        return (0, False)

    elif question.type == "single_choice":
        # Tek bir choice doğru
        correct_choice = db.query(QuestionChoice).filter_by(question_id=question.id, is_correct=True).first()
        if not correct_choice:
            return (0, False)
        if len(selected_texts) == 1 and selected_texts[0] == correct_choice.choice_text:
            return (question.points, True)
        return (0, False)

    elif question.type == "multiple_choice":
        correct_choices = db.query(QuestionChoice).filter_by(
            question_id=question.id, 
            is_correct=True
        ).all()
        correct_texts = set(c.choice_text.strip().lower() for c in correct_choices)
        user_set = set(txt.strip().lower() for txt in selected_texts)

        # Yanlış şık seçilirse direkt 0
        if not user_set.issubset(correct_texts):
            return (0, False)

        # Doğru seçilen sayısı
        correct_selected = len(user_set & correct_texts)
        total_correct = len(correct_texts)

        if total_correct == 0:
            return (0, False)

        # Kısmi puan hesapla
        partial_score = int(question.points * (correct_selected / total_correct))
        is_full = (partial_score == question.points)
        return (partial_score, is_full)

    elif question.type == "ordering":
        all_choices = db.query(QuestionChoice).filter_by(question_id=question.id).all()
        mismatch = False
        
        # Kullanıcı girdilerini normalize et
        normalized_selected = [x.strip().lower() for x in selected_texts]
        
        for c in all_choices:
            if c.correct_position is None:
                continue
            # choice_text'i normalize et
            normalized_choice = c.choice_text.strip().lower()
            try:
                user_index = normalized_selected.index(normalized_choice)
                if user_index != c.correct_position:
                    mismatch = True
                    break
            except ValueError:
                mismatch = True
                break

        if mismatch:
            return (0, False)
        else:
            return (question.points, True)

    # default
    return (0, False)
