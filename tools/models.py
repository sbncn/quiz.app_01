# tools/models.py
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from tools.database import Base
from datetime import datetime

# Association Table for Exam and Question
exam_question_association = Table(
    'exam_question_association',
    Base.metadata,
    Column('exam_id', PGUUID(as_uuid=True), ForeignKey('exams.exam_id'), primary_key=True),
    Column('question_id', PGUUID(as_uuid=True), ForeignKey('questions.id'), primary_key=True)
)

class School(Base):
    __tablename__ = "schools"
    school_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)

    # relationships
    users = relationship("User", back_populates="school")
    exams = relationship("Exam", back_populates="school")
    statistics = relationship("Statistics", back_populates="school")


class User(Base):
    __tablename__ = "users"
    user_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(Text, nullable=False)

    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    role = Column(String(50), nullable=False)

    attempts = Column(Integer, default=0)
    last_attempt_date = Column(DateTime, nullable=True)
    score1 = Column(Float, default=0)
    score2 = Column(Float, default=0)
    score_avg = Column(Float, default=0)

    class_name = Column(String(50), nullable=False)
    registered_section = Column(String(50), nullable=True)

    school_id = Column(PGUUID(as_uuid=True), ForeignKey("schools.school_id", ondelete='CASCADE'), nullable=False)
    school = relationship("School", back_populates="users")

    exams = relationship("Exam", back_populates="user", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    external_id = Column(String, unique=True, nullable=False)
    section = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    points = Column(Integer, nullable=False, default=1)
    type = Column(String(50), nullable=False)

    # Soru ile ilişkili choices
    question_choices = relationship("QuestionChoice", back_populates="question", cascade="all, delete-orphan")

    # exam_question_association ile many-to-many
    exams = relationship(
        "Exam",
        secondary=exam_question_association,
        back_populates="selected_questions"
    )


class QuestionChoice(Base):
    """
    Her bir soru için 1..N adet şık satırı:
      - single/multiple/true_false => is_correct bool
      - ordering => correct_position (int); is_correct ise isterseniz None
    """
    __tablename__ = "question_choices"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    question_id = Column(PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete='CASCADE'), nullable=False)
    choice_text = Column(Text, nullable=False)

    is_correct = Column(Boolean, default=False)  # T/F, single, multiple
    correct_position = Column(Integer, nullable=True)  # ordering

    question = relationship("Question", back_populates="question_choices")


class Exam(Base):
    __tablename__ = "exams"
    exam_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.user_id", ondelete='CASCADE'), nullable=False)

    class_name = Column(String(50), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)

    school_id = Column(PGUUID(as_uuid=True), ForeignKey("schools.school_id", ondelete='CASCADE'), nullable=False)
    school = relationship("School", back_populates="exams")

    user = relationship("User", back_populates="exams")

    # exam_answers -> her soru için 1 adet
    exam_answers = relationship("ExamAnswer", back_populates="exam", cascade="all, delete-orphan")

    # Seçilen sorular
    selected_questions = relationship(
        "Question",
        secondary=exam_question_association,
        back_populates="exams"
    )


class ExamAnswer(Base):
    __tablename__ = "exam_answers"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    exam_id = Column(PGUUID(as_uuid=True), ForeignKey("exams.exam_id", ondelete='CASCADE'), nullable=False)
    question_id = Column(PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete='CASCADE'), nullable=False)

    points_earned = Column(Integer, default=0)  # bu soru için kazanılan puan

    exam = relationship("Exam", back_populates="exam_answers")

    # Bu cevaba ait seçilen choices
    user_choices = relationship("UserChoice", back_populates="exam_answer", cascade="all, delete-orphan")


class UserChoice(Base):
    """
    Öğrencinin bu soru için hangi choice(lar)ı işaretlediğini kaydeder.
    - multiple choice: bir exam_answer_id için birden fazla user_choice
    - single choice / true_false: bir tane user_choice
    - ordering: birden fazla user_choice; user_position ile hangi sırada olduğunu tutabiliriz.
    """
    __tablename__ = "user_choices"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    exam_answer_id = Column(PGUUID(as_uuid=True), ForeignKey("exam_answers.id", ondelete='CASCADE'), nullable=False)
    question_choice_id = Column(PGUUID(as_uuid=True), ForeignKey("question_choices.id", ondelete='CASCADE'), nullable=True)

    user_position = Column(Integer, nullable=True)  # ordering tipinde kullanıcı sıralama

    exam_answer = relationship("ExamAnswer", back_populates="user_choices")
    # question_choice'a bir ilişki de istenirse eklenebilir
    # question_choice = relationship("QuestionChoice", ...)

class Statistics(Base):
    __tablename__ = "statistics"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    class_name = Column(String(50), nullable=False)
    section_number = Column(Integer, nullable=False)
    correct_questions = Column(Integer, default=0)
    wrong_questions = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    section_percentage = Column(Float, default=0.0)

    school_id = Column(PGUUID(as_uuid=True), ForeignKey("schools.school_id"), nullable=False)
    school = relationship("School", back_populates="statistics")
