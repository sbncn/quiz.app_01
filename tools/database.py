# tools/database.py
import os
import sys
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()

retries = 5
while retries > 0:
    try:
        engine = create_engine(DATABASE_URL, future=True)
        logger.info("Database engine created successfully.")
        break
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        retries -= 1
        time.sleep(5)
else:
    logger.critical("Failed to connect to the database after multiple attempts.")
    sys.exit(1)  # Exit the application

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from tools.models import User, Question, Exam, ExamAnswer, Statistics, School, QuestionChoice

    from migrate_questions import main as migrate_questions_main
    from tools.user import create_admin_user

    try:
        logger.info("Starting database initialization...")
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully.")

        # Seed initial data
        seed_initial_data()

        # Create admin user
        create_admin_user(engine)

        # Migrate questions
        with next(get_db()) as db:
            migrate_questions_main()

        logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        sys.exit(1)

def seed_initial_data():
    from tools.models import School
    with next(get_db()) as db:
        default_school = db.query(School).filter(School.name == "DefaultSchool").first()
        if not default_school:
            new_school = School(name="DefaultSchool")
            db.add(new_school)
            db.commit()
            db.refresh(new_school)
            logger.info("DefaultSchool added.")
        else:
            logger.info("DefaultSchool already exists.")
