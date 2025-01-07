import random
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()
# Global Constants
BASE_DIR = os.getenv('BASE_DIR', '/app')  # Default to '/app' if BASE_DIR isn't defined
SECTION_NAMES = ["English", "Computer", "History", "Geography"]


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
class Question:
    def __init__(self, section, answer, question_id, question_text, options, question_type, question_score):
        self.section = section  # Section number
        self.answer = answer  # Correct answer
        self.question_id = question_id
        self.question_text = question_text
        self.options = options
        self.question_type = question_type
        self.section_name = SECTION_NAMES[section - 1]  # Section name (1-indexed)
        self.question_score = question_score  # Default question score
        self.questions = self.load_questions()  # Load questions
        self.answers = self.load_answers()  # Load answers
        self.randomized_questions = self.randomize_questions()  # Shuffle questions
        self.current_question_index = 0  # Track current question index
        self.validate_question_format()  # Validate question formats

    def load_questions(self):
        """Load questions for the selected section from the database."""
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, section_name, question_id, question_text, question_type, score
                FROM questions
                WHERE section_name = %s
            """, (self.section_name,))
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "section_name": row[1],
                    "question_id": row[2],
                    "question_text": row[3],
                    "question_type": row[4],
                    "score": row[5]
                } for row in rows
            ]
        except Exception as e:
            print(f"Error loading questions from database: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

    def load_answers(self):
        """Load answers for the selected section from the database."""
        conn = get_db_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT q.id, a.answer
                FROM answers a
                JOIN questions q ON a.question_id = q.id
                WHERE q.section_name = %s
            """, (self.section_name,))
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}
        except Exception as e:
            print(f"Error loading answers from database: {e}")
            return {}
        finally:
            cursor.close()
            conn.close()

    def randomize_questions(self):
        """Shuffle questions randomly."""
        if not self.questions:
            print(f"No questions available for section '{self.section_name}'.")
            return []
        random.shuffle(self.questions)
        return self.questions

    def validate_question_format(self):
        """Validate the format of all loaded questions."""
        for question in self.questions:
            if not self.validate_question_structure(question):
                print(f"Invalid question format for question ID {question.get('id')}.")

    @staticmethod
    def validate_question_structure(question):
        """Validate the structure of a single question."""
        required_keys = {"id", "question_text", "question_type", "score"}
        return required_keys.issubset(question.keys())

    def ask_question(self):
        """Ask the current question to the user."""
        if self.current_question_index >= len(self.randomized_questions):
            print("All questions answered!")
            return None

        question = self.randomized_questions[self.current_question_index]
        self.current_question_index += 1

        user_answer = self.handle_question(question)
        return self.evaluate_answer(question, user_answer)

    def handle_question(self, question):
        """Handle a question based on its type."""
        question_type = question.get("question_type", "Unknown")
        print(f"Question: {question.get('question_text')}")
        print(f"Question Type: {question_type}")

        try:
            if question_type == "True-False":
                return self.handle_true_false(question)
            elif question_type == "Multiple-Choice":
                return self.handle_multiple_choice(question)
            elif question_type == "Multiple-Answer":
                return self.handle_multiple_answer(question)
            elif question_type == "Ordering":
                return self.handle_ordering(question)
            else:
                print(f"Unknown question type: {question_type}")
                return None
        except Exception as e:
            print(f"Error handling question: {e}")
            return None

    def handle_true_false(self, question):
        print("Options: 1. True / 2. False")
        return input("Your answer (1 or 2): ").strip()

    def handle_multiple_choice(self, question):
        for idx, option in enumerate(question.get("options", []), start=1):
            print(f"{idx}. {option}")
        return input("Please select one option: ").strip()

    def handle_multiple_answer(self, question):
        for idx, option in enumerate(question.get("options", []), start=1):
            print(f"{idx}. {option}")
        return input("Please select all that apply (e.g., 1,3): ").strip()

    def handle_ordering(self, question):
        print(f"Words to order: {', '.join(question.get('options', []))}")
        return input("Enter the correct order (e.g., 2,1,4,3): ").strip()

    def evaluate_answer(self, question, user_answer):
        """Evaluate the user's answer."""
        answer = self.answers.get(question["id"])  # Doğru cevap veritabanından geliyor
        if answer is None:
            print(f"No correct answer found for question {question['id']}.")
            return 0
        
        question_type = question.get("question_type", "Unknown")
        
        if question_type == "Multiple-Choice":
            # Single correct answer (e.g., "1")
            is_correct = user_answer.strip() == str(answer).strip()
        
        elif question_type == "Multiple-Answer":
            # Multiple correct answers (e.g., "1,3")
            user_answers = set(user_answer.split(","))
            correct_answers = set(str(answer).split(","))
            is_correct = user_answers == correct_answers
        
        elif question_type == "Ordering":
            # Check if order matches (e.g., "1,2,3,4")
            is_correct = user_answer.strip() == str(answer).strip()
        
        elif question_type == "True-False":
            # True/False questions (e.g., "1" for True, "2" for False)
            is_correct = user_answer.strip() == str(answer).strip()
        
        else:
            print(f"Unknown question type: {question_type}")
            return 0
        
        return question.get("score", 0) if is_correct else 0