# tools/statistics_utils.py

from sqlalchemy.orm import Session
from tools.models import Statistics

def update_statistics(db: Session, school_id, class_name, section_correct, section_wrong, section_scores):
    for section in section_correct.keys():
        stat = db.query(Statistics).filter(
            Statistics.school_id == school_id,
            Statistics.class_name == class_name,
            Statistics.section_number == section
        ).first()

        c = section_correct[section]
        w = section_wrong[section]
        s = section_scores[section]

        if not stat:
            total_questions = c + w
            section_percentage = (c / total_questions * 100) if total_questions > 0 else 0
            stat = Statistics(
                school_id=school_id,
                class_name=class_name,
                section_number=section,
                correct_questions=c,
                wrong_questions=w,
                average_score=s,
                section_percentage=section_percentage
            )
            db.add(stat)
        else:
            stat.correct_questions += c
            stat.wrong_questions += w
            old_avg = stat.average_score
            if old_avg == 0:
                stat.average_score = s
            else:
                stat.average_score = (old_avg + s) / 2

            new_total_correct = stat.correct_questions
            new_total_wrong = stat.wrong_questions
            new_total_questions = new_total_correct + new_total_wrong
            stat.section_percentage = (new_total_correct / new_total_questions * 100) if new_total_questions > 0 else 0

        db.commit()
