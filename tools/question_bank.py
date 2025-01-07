import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from the .env file
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

class QuestionBank:
    def __init__(self, db_config):
        self.db_config = db_config

    def get_questions_by_section(self, section_name):
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, question_text
                FROM questions
                WHERE section_name = %s
            """, (section_name,))

            questions = cursor.fetchall()
            conn.close()
            return questions
        except psycopg2.Error as e:
            print(f"Database error while fetching questions: {e}")
            return []

    def load_questions(self):
        """
        Load questions from the database.

        :return: Dictionary with sections as keys and their respective questions as values.
        """
        questions = {}
        conn = self.get_db_connection()
        if conn is None:
            return questions

        try:
            cursor = conn.cursor()
            for section_id in range(1, 5):
                cursor.execute("""
                    SELECT id, section_name, question_id, question_text, question_type, score
                    FROM questions
                    WHERE section = %s
                """, (section_id,))
                rows = cursor.fetchall()

                # Convert fetched data into a list of dictionaries
                questions[f"section{section_id}"] = [
                    {
                        "id": row[0],
                        "section_name": row[1],
                        "question_id": row[2],
                        "question_text": row[3],
                        "question_type": row[4],
                        "score": row[5],
                    }
                    for row in rows
                ]
            return questions

        except psycopg2.Error as e:
            print(f"Error loading questions from database: {e}")
            return questions
        finally:
            cursor.close()
            conn.close()

    def add_question(self, section):
        """
        Add a new question to a specific section based on type.

        :param section: The section to which the question belongs.
        """
        conn = self.get_db_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()

            # Get the question details
            print("\nSelect the question type:")
            print("1. True-False")
            print("2. Multiple-Choice")
            print("3. Multiple-Answer")
            print("4. Ordering")
            question_type = input("Enter the number corresponding to the question type: ").strip()

            question_text = input("Enter the question text: ").strip()
            score = int(input("Enter the score for this question: ").strip())

            if question_type == "1":
                options = ["True", "False"]
                correct_answer = input("Enter the correct answer (True/False): ").strip()
                question_type = "True-False"

            elif question_type == "2":
                options = input("Enter options (comma-separated): ").strip()
                correct_answer = input("Enter the correct answer: ").strip()
                question_type = "Multiple-Choice"

            elif question_type == "3":
                options = input("Enter options (comma-separated): ").strip()
                correct_answers = input("Enter the correct answers (comma-separated): ").strip()
                correct_answer = correct_answers  # Store multiple answers
                question_type = "Multiple-Answer"

            elif question_type == "4":
                words = input("Enter the items to order (comma-separated): ").strip()
                correct_answer = words  # Store ordered items
                question_type = "Ordering"

            else:
                print("Invalid question type. Aborting addition.")
                return

            # Insert the new question into the database
            cursor.execute("""
                INSERT INTO questions (section, question_text, question_type, correct_answer, score)
                VALUES (%s, %s, %s, %s, %s)
            """, (section, question_text, question_type, correct_answer, score))

            conn.commit()
            print("Question added successfully!")

        except psycopg2.Error as e:
            print(f"Error adding question to the database: {e}")

        finally:
            cursor.close()
            conn.close()

    def update_question(self, section, question_id):
        """
        Update an existing question in the database.

        :param section: The section of the question.
        :param question_id: The ID of the question to update.
        """
        conn = self.get_db_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()

            # Fetch the current question details
            cursor.execute("""
                SELECT question_text, question_type, correct_answer, score
                FROM questions
                WHERE id = %s AND section = %s
            """, (question_id, section))
            question = cursor.fetchone()

            if not question:
                print(f"Question with ID {question_id} not found in section {section}.")
                return

            # Show the current details
            print(f"Current Question: {question}")

            # Get updated details
            question_text = input(f"Enter updated question text (leave blank to keep current): ").strip()
            question_text = question_text if question_text else question[0]

            score = input(f"Enter updated score (leave blank to keep current): ").strip()
            score = int(score) if score else question[3]

            # Update the question
            cursor.execute("""
                UPDATE questions
                SET question_text = %s, score = %s
                WHERE id = %s AND section = %s
            """, (question_text, score, question_id, section))
            conn.commit()
            print("Question updated successfully!")

        except psycopg2.Error as e:
            print(f"Error updating question: {e}")

        finally:
            cursor.close()
            conn.close()

    def delete_question(self, section, question_id):
        """
        Delete a question from the database.

        :param section: The section of the question.
        :param question_id: The ID of the question to delete.
        """
        conn = self.get_db_connection()
        if conn is None:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM questions
                WHERE id = %s AND section = %s
            """, (question_id, section))
            conn.commit()
            print("Question deleted successfully!")

        except psycopg2.Error as e:
            print(f"Error deleting question: {e}")

        finally:
            cursor.close()
            conn.close()

    def question_menu(self):
        """
        Show the menu for managing questions.
        """
        print("\nAvailable Sections: section1, section2, section3, section4")
        section = input("Select a section to manage (e.g., 'section1'): ").strip()

        while True:
            print("\n=== Question Menu ===")
            print("1. Add a question")
            print("2. Update a question")
            print("3. Delete a question")
            print("4. Back to Teacher Menu")

            choice = input("Choose an option (1-4): ").strip()

            if choice == "1":
                self.add_question(section)

            elif choice == "2":
                question_id = int(input("Enter the ID of the question to update: ").strip())
                self.update_question(section, question_id)

            elif choice == "3":
                question_id = int(input("Enter the ID of the question to delete: ").strip())
                self.delete_question(section, question_id)

            elif choice == "4":
                print("Returning to Teacher Menu.")
                break

            else:
                print("Invalid choice. Please try again.")