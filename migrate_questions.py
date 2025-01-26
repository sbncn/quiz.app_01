# tools/migrate_questions.py

import json
from pathlib import Path
from sqlalchemy.orm import Session
from tools.database import get_db
from tools.models import Question, QuestionChoice

# Kaynak dosyaların varsayılan yolları
QUESTIONS_DIR = Path("questions")            # Örn: "questions_section1.json" ...
ANSWERS_FILE = Path("answers/answers.json")  # Örn: "answers.json"

def load_json(filepath: Path):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def questions_already_migrated(db: Session) -> bool:
    """Daha önce question tablosu dolu mu?"""
    existing = db.query(Question).first()
    return existing is not None

def main():
    with next(get_db()) as db:
        if questions_already_migrated(db):
            print("Questions already migrated. Skipping.")
            return
        
        # 1) Tüm cevapları (dictionary) okuyalım
        if not ANSWERS_FILE.exists():
            print(f"Answers file '{ANSWERS_FILE}' not found. Can't set correct answers.")
            answers_data = {}
        else:
            answers_data = load_json(ANSWERS_FILE)  # dict: { "q_ext_id": str veya list }
        
        # 2) Soru dosyalarını (section=1..4) sırayla işle
        for section in range(1, 5):
            q_file = QUESTIONS_DIR / f"questions_section{section}.json"
            if not q_file.exists():
                print(f"{q_file} not found, skipping.")
                continue
            
            q_data = load_json(q_file)
            questions_list = q_data.get("questions", [])
            if not questions_list:
                print(f"No questions found in {q_file}, skipping.")
                continue
            
            for q_item in questions_list:
                ext_id = q_item["id"]
                existing_q = db.query(Question).filter(Question.external_id == ext_id).first()
                if existing_q:
                    print(f"Question with external_id={ext_id} already exists. Skipping.")
                    continue
                
                # Soru oluştur
                new_q = Question(
                    external_id=ext_id,
                    section=q_item["section"],
                    question=q_item["question"],
                    points=q_item["points"],
                    type=q_item["type"]
                )
                db.add(new_q)
                db.commit()
                db.refresh(new_q)
                
                # SORU TİPİ
                q_type = new_q.type  # "true_false", "single_choice", "multiple_choice", "ordering"
                
                # Cevabı answers_data'dan alalım (tek str veya list olabilir)
                raw_answer = answers_data.get(ext_id, None)
                
                # JSON'daki "options"/"choices"
                # Bazı JSONlarda "options" yerine "choices" olabilir, check:
                options_list = q_item.get("options") or q_item.get("choices") or []
                
                if q_type == "true_false":
                    # T/F => genellikle 2 opsiyon ("True","False")
                    # Yoksa default
                    if not options_list:
                        options_list = ["True", "False"]
                    
                    # Hangisi doğru?
                    # raw_answer string -> "True" veya "False"
                    for opt in options_list:
                        is_corr = False
                        if raw_answer and isinstance(raw_answer, str):
                            if opt.strip().lower() == raw_answer.strip().lower():
                                is_corr = True
                        # question_choice kaydet
                        qc = QuestionChoice(
                            question_id=new_q.id,
                            choice_text=opt,
                            is_correct=is_corr
                        )
                        db.add(qc)
                    db.commit()
                
                elif q_type == "single_choice":
                    # Tek bir doğru
                    # options_list = ["6", "9", "12", "15"] vs.
                    # raw_answer = "9"
                    for opt in options_list:
                        is_corr = False
                        if raw_answer and isinstance(raw_answer, str):
                            if opt.strip().lower() == raw_answer.strip().lower():
                                is_corr = True
                        qc = QuestionChoice(
                            question_id=new_q.id,
                            choice_text=opt,
                            is_correct=is_corr
                        )
                        db.add(qc)
                    db.commit()
                
                elif q_type == "multiple_choice":
                    # Birden fazla doğru
                    # raw_answer = list, örn. ["Pythagoras","Euclid"]
                    correct_set = set()
                    if raw_answer:
                        if isinstance(raw_answer, list):
                            correct_set = set(a.strip().lower() for a in raw_answer)
                        else:
                            # belki single str "A,B" vs.
                            correct_set = set(x.strip().lower() for x in raw_answer.split(","))
                    
                    for opt in options_list:
                        is_corr = False
                        if opt.strip().lower() in correct_set:
                            is_corr = True
                        
                        qc = QuestionChoice(
                            question_id=new_q.id,
                            choice_text=opt,
                            is_correct=is_corr
                        )
                        db.add(qc)
                    db.commit()
                
                elif q_type == "ordering":
                    # Ordering => "options": ["3","1","4","2"]
                    # raw_answer => ["1","2","3","4"] (doğru sıralama)
                    # Her choice_text'e correct_position verelim
                    # Yani new_q'nin "options" sıralaması UI'da "random" olabilir ama JSON'da tipik olarak orijinal sırasıyla verilir.
                    # Biz correct_position'ı raw_answer'daki index'e göre setleyeceğiz.
                    # E.g. if raw_answer = ["1","2","3","4"], then "1" -> correct_position=0, "2" -> 1, ...
                    correct_pos_map = {}
                    if raw_answer and isinstance(raw_answer, list):
                        # create a map: text -> position
                        for idx, val in enumerate(raw_answer):
                            correct_pos_map[val.strip().lower()] = idx
                    
                    # ekleyelim
                    for opt in options_list:
                        cpos = None
                        # opt'i correct_pos_map'ta bul
                        # Mesela "3" -> ?
                        key = opt.strip().lower()
                        if key in correct_pos_map:
                            cpos = correct_pos_map[key]
                        
                        qc = QuestionChoice(
                            question_id=new_q.id,
                            choice_text=opt,
                            is_correct=False,       # ordering'de is_correct tipik olarak false
                            correct_position=cpos   # asıl kritik alan
                        )
                        db.add(qc)
                    db.commit()
                
                else:
                    # bilinmeyen tip
                    print(f"Unknown question type: {q_type} - no choices created.")
                
                print(f"Migrated Q: {new_q.external_id} ({new_q.question[:30]}...)")
        
        print("Migration completed successfully.")

if __name__ == "__main__":
    main()
