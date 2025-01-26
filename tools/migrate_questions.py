# tools/migrate_questions.py

import json
from pathlib import Path
from sqlalchemy.orm import Session
from tools.database import get_db
from tools.models import Question, Answer

QUESTIONS_DIR = Path("questions")           # "questions_section1.json" vs.
ANSWERS_FILE = Path("answers/answers.json") # "answers.json" vs.

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def questions_already_migrated(db: Session) -> bool:
    existing = db.query(Question).first()
    return existing is not None

def main():
    with next(get_db()) as db:
        if questions_already_migrated(db):
            print("Questions already migrated. Skipping.")
            return
        
        # 1) Soruları ekle
        for section in range(1, 5):
            q_file = QUESTIONS_DIR / f"questions_section{section}.json"
            if not q_file.exists():
                print(f"{q_file} not found, skipping.")
                continue
            q_data = load_json(q_file)
            questions_list = q_data.get("questions", [])
            for q_item in questions_list:
                ext_id = q_item["id"]
                existing_q = db.query(Question).filter(Question.external_id == ext_id).first()
                if existing_q:
                    print(f"Question with external_id={ext_id} already exists. Skipping.")
                    continue
                new_q = Question(
                    external_id=ext_id,
                    section=q_item["section"],
                    question=q_item["question"],
                    points=q_item["points"],
                    type=q_item["type"]
                )
                db.add(new_q)
                db.commit()
        
        # 2) Cevapları ekle
        if not ANSWERS_FILE.exists():
            print("Answers file not found. Skipping answers.")
            return
        a_data = load_json(ANSWERS_FILE)
        questions_in_db = db.query(Question).all()
        for q in questions_in_db:
            ext_id = q.external_id
            if ext_id in a_data:
                ans_value = a_data[ext_id]
                if isinstance(ans_value, list):
                    correct_answer = ",".join(str(a).strip() for a in ans_value)
                else:
                    correct_answer = str(ans_value).strip()
                new_a = Answer(question_id=q.id, correct_answer=correct_answer)
                db.add(new_a)
                db.commit()
            else:
                print(f"No answer found for question external_id={ext_id}")

        print("Migration completed successfully.")

if __name__ == "__main__":
    main()
