from tools.timer import Timer
from tools.user import User
from tools.questions import Question
import psycopg2
import os
from dotenv import load_dotenv


load_dotenv()

# db_config için ortam değişkenlerinden verileri al
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Veritabanı bağlantısı kurmak için bir fonksiyon
def get_db_connection():
    try:
        # Veritabanı bağlantısını sağla
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password']
        )
        print("Database connection successful.")
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

class Exam:
    def __init__(self, user, db_config):
        self.user = user
        self.db_config = db_config
        self.questions = []  # Will be populated with questions from the database
        self.user_answers = []
        self.exam_active = False

    def fetch_questions(self):
        """
        Fetch questions and correct answers from the database and populate the exam.
        """
        try:
            # Connect to the PostgreSQL database
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Fetch questions and their correct answers
            cursor.execute("""
                SELECT 
                    q.id AS question_id,
                    q.question_text,
                    q.options,
                    q.question_type,
                    a.answer
                FROM 
                    questions q
                LEFT JOIN 
                    answers a 
                ON 
                    q.id = a.question_id
                ORDER BY 
                    RANDOM()
                LIMIT 10;
            """)
            question_data = cursor.fetchall()

            # Populate questions into the exam
            for data in question_data:
                question_id, question_text, options, question_type, answer = data
                question = Question(question_id, question_text, options, question_type, answer)
                self.questions.append(question)

        except psycopg2.Error as e:
            print(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def start_exam(self):
        print(f"\nWelcome {self.user.username}! Your exam is starting.")
        self.exam_active = True

        # Timer setup: start the timer for the exam
        timer = Timer()
        timer.start()

        correct_answers = 0

        # Loop through each question, ask it and store the answers
        for index, question in enumerate(self.questions):
            print(f"\nQuestion {index + 1}:")
            score = question.ask_question()  # Ask the question and calculate score
            self.user_answers.append(score)
            correct_answers += (score / question.question_score)  # Accumulate correct answers for final score

        # Calculate total score for the exam
        print("\nExam Completed!")
        total_score = sum(self.user_answers)
        print(f"Total Score: {total_score:.2f}")

        # Store results in the database
        self.save_exam_results(total_score, correct_answers)

        # Stop timer and print duration
        timer.stop()
        print(f"Exam completed in {timer.elapsed_time:.2f} seconds.")

    def save_exam_results(self, total_score, correct_answers):
        """
        Save the exam results in the database for this user.
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Store the results in the `results` table
            cursor.execute("""
                INSERT INTO results (student_number, exam_attempt, score, true_count, false_count)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.user.student_number, 1, total_score, correct_answers, len(self.questions) - correct_answers))

            # Commit the transaction
            conn.commit()

        except psycopg2.Error as e:
            print(f"Database error: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        print("Results saved to the database.")