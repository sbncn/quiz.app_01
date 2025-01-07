import random
import json
import psycopg2
from psycopg2 import sql
from tools.user import User
from tools.setup import get_db_connection, db_config
from tools.user import hash_password
from tools.question_bank import QuestionBank
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

def generate_unique_id(cursor, role):
    """
    Generates a unique ID based on the role (student or teacher) using PostgreSQL.
    
    :param cursor: PostgreSQL cursor object.
    :param role: The role for the user (student or teacher).
    :return: A unique ID as a string.
    """
    prefix = "S" if role == "student" else "T"
    while True:
        new_id = f"{prefix}{random.randint(1000, 9999)}"
        cursor.execute("""
            SELECT COUNT(*) FROM users
            WHERE student_number = %s OR teacher_id = %s
        """, (new_id, new_id))
        if cursor.fetchone()[0] == 0:
            return new_id

def signup(db_config):
    """
    Signs up a new user and saves it into the PostgreSQL database.
    
    :param db_config: Dictionary containing the database configuration.
    """
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return

    print("\n--- Add New User ---")
    username = input("Enter username: ").strip()
    name = input("Enter name: ").strip()
    surname = input("Enter surname: ").strip()
    password = input("Enter password: ").strip()
    role = input("Enter role (student/teacher): ").strip().lower()

    if role not in ["student", "teacher"]:
        print("Invalid role. Please choose 'student' or 'teacher'.")
        return

    unique_id = generate_unique_id(cursor, role)

    if role == "student":
        school_name = input("Enter school name: ").strip()
        class_number = input("Enter class number: ").strip()
        student_number = unique_id
        teacher_id = None
        subject = None
    elif role == "teacher":
        subject = input("Enter subject: ").strip()
        school_name = None
        class_number = None
        student_number = None
        teacher_id = unique_id

    is_admin = input("Is this user an admin? (yes/no): ").strip().lower() == "yes"

    hashed_password = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO users (
                username, name, surname, password, role, is_admin,
                subject, school_name, class_number, student_number, teacher_id,
                attempts, max_attempts
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            username, name, surname, hashed_password, role, is_admin,
            subject, school_name, class_number, student_number, teacher_id,
            0, 3
        ))
        conn.commit()
        print(f"User '{username} {name} {surname}' with ID '{unique_id}' has been created.")
    except psycopg2.Error as e:
        print(f"Error saving user to database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def login(db_config):
    """
    Allows a user to log in by validating credentials from the PostgreSQL database.
    
    :param db_config: Dictionary containing the database configuration.
    """
    print("\n--- Login ---")
    user_id = input("Enter your username: ").strip()

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

    try:
        cursor.execute("""
            SELECT id, username, name, surname, student_number, password, 
                   teacher_id, role, subject, school_name, class_number, is_admin, attempts, max_attempts
            FROM users
            WHERE username = %s
        """, (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            print("User not found. Please sign up first.")
            return None

        attempts, max_attempts = user_data[12], user_data[13]
        if attempts >= max_attempts:
            print("You have exceeded the maximum number of login attempts. Please try again later.")
            return None

        user = User(
            id=user_data[0],
            username=user_data[1],
            password=user_data[5],
            name=user_data[2],
            surname=user_data[3],
            student_number=user_data[4],
            teacher_id=user_data[6],
            role=user_data[7],
            subject=user_data[8],
            school_name=user_data[9],
            class_number=user_data[10],
            is_admin=user_data[11],
            attempts = attempts,
            max_attempts = max_attempts
        )

        print(f"Welcome {user.name} {user.surname} ({user.role.capitalize()}).")

        password_try = 0
        while password_try < 3:
            password = input("Enter your password: ").strip()
            hashed_input_password = hash_password(password)

            if hashed_input_password == user.password:
                print("Login successful!")
                cursor.execute("""
                    UPDATE users
                    SET attempts = 0
                    WHERE id = %s
                """, (user.id,))
                conn.commit()

                if user.role == "teacher":
                    teacher_menu(user, db_config)
                elif user.role == "student":
                    student_menu(user, db_config)
                elif user.role == "admin":
                    admin_menu(user, db_config)

                return user
            else:
                print("Incorrect password. Please try again.")
                password_try += 1

        cursor.execute("""
            UPDATE users
            SET attempts = attempts + 1
            WHERE id = %s
        """, (user.id,))
        conn.commit()

        print("Too many failed login attempts.")
        return None

    except psycopg2.Error as e:
        print(f"Error during login process: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def normalize_section_name(section):
    """Normalize the section name for consistent database queries."""
    return section.strip().lower()
def get_user_answers(questions):
    """
    Function to get user answers.
    Allows entering option numbers or directly as text if needed.
    Handles multiple answers by separating with commas.
    """
    user_answers = {}
    for question in questions:
        question_id, question_text, options, question_type = question
        
        # Print the question text
        print(f"Question: {question_text}")
        
        # Display the options if available
        if options:
            if isinstance(options, list):
                options_list = options
            else:  # Otherwise, assume it's a string and split it
                options_list = options.split('|')

            for i, option in enumerate(options_list, start=1):
                print(f"{i}. {option.strip()}")

        # Get user answer
        while True:
            try:
                # Allow input as either numbers (e.g., "1,2") or text (e.g., "option1, option2")
                answer = input("Your answer (enter numbers or text, separated by commas): ").strip()

                if not answer:
                    print("Invalid input. Please try again.")
                    continue

                # Process user input as numbers or text
                if answer.replace(',', '').isdigit():  # If input is all numbers
                    answer_numbers = [int(a) for a in answer.split(',')]  # Convert to integers
                    if all(1 <= a <= len(options_list) for a in answer_numbers):  # Validate range
                        # Map numbers to actual answers for consistency
                        mapped_answers = [options_list[a - 1].strip().lower() for a in answer_numbers]
                        user_answers[question_id] = mapped_answers
                        break
                    else:
                        print("Invalid option number(s). Please try again.")
                else:  # Assume input is text
                    answer_texts = [a.strip().lower() for a in answer.split(',')]
                    if all(a in [o.strip().lower() for o in options_list] for a in answer_texts):  # Validate text
                        user_answers[question_id] = answer_texts
                        break
                    else:
                        print("Invalid option text(s). Please try again.")
            except Exception as e:
                print(f"Error processing your input: {e}. Please try again.")
                
    return user_answers


def check_answer(user_answer, answer, question_type):
    """
    Compares user answer with the correct answer.
    Handles multiple answers and ordering questions.
    """
    if not answer:  # Eğer doğru cevap yoksa
        print("No correct answer available for this question.")
        return False

    # Normalize both user answers and correct answers for comparison
    user_answer = [str(a).strip().lower() for a in user_answer]
    answer = [str(a).strip().lower() for a in answer]

    if question_type == 'multiple':  # Birden fazla doğru cevabı olan sorular
        return set(user_answer) == set(answer)
    
    elif question_type == 'ordering':  # Sıralama sorusu
        return user_answer == answer  # Kullanıcının sıralaması doğruysa
    else:  # Tek doğru cevaplı soru
        return user_answer == answer  # Kullanıcının cevabı doğruysa


def take_exam(user, db_config):
    """
    Allows the user to take an exam, tracking results and limiting the number of attempts.
    """
    print("\n--- Take Exam ---")
    overall_score = 0.0
    sections = ['English', 'Computer', 'History', 'Geography']

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        print("Database connection successful.")
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return

    try:
        # Fetch user attempts
        cursor.execute(""" 
            SELECT attempts
            FROM users
            WHERE student_number = %s
        """, (user.student_number,))
        user_data = cursor.fetchone()

        if not user_data:
            print("User not found in the database.")
            return

        attempts = user_data[0]
        max_attempts = 2
        print(f"User data fetched: attempts={attempts}, max_attempts={max_attempts}")

        # Check if user has attempts left
        if attempts >= max_attempts:
            print(f"You have no remaining exam attempts. Maximum attempts ({max_attempts}) reached.")
            return  # Sınav işlemi durduruluyor.

        # Loop through exam sections
        for section in sections:
            print(f"\nStarting exam for {section} (Attempt {attempts + 1}/{max_attempts})")

            normalized_section = normalize_section_name(section)

            # Fetch 5 random questions for the section
            cursor.execute("""
                SELECT q.id, q.question_text, q.options, q.question_type
                FROM questions q
                WHERE LOWER(q.section_name) = %s
                ORDER BY RANDOM()  -- Fetch random questions
                LIMIT 5
            """, (normalized_section,))

            questions = cursor.fetchall()
            print(f"Fetched {len(questions)} questions for the {section} section.")

            if not questions:
                print(f"No questions available for the {section} section.")
                continue

            # Fetch the correct answers for the questions
            question_ids = [q[0] for q in questions]  # Extract question IDs
            cursor.execute("""
                SELECT q.id, a.answer, q.question_type
                FROM questions q
                JOIN answers a ON q.id = a.question_id
                WHERE q.id IN %s
                ORDER BY q.id, a.id
            """, (tuple(question_ids),))  # Fetch answers for these question IDs

            question_details = cursor.fetchall()

            # Create a dictionary to hold questions with their correct answers and types
            detailed_questions = {}
            for q in question_details:
                question_id, answer, question_type = q
                detailed_questions[question_id] = {'answer': answer, 'question_type': question_type}

            # Get the user answers for the questions
            user_answers = get_user_answers(questions)

            score = 0
            total_questions = len(questions)
            for question in questions:
                question_id, question_text, options, question_type = question
                user_answer = user_answers.get(question_id, None)

                # Retrieve the correct answer and question type
                correct_answer = detailed_questions.get(question_id, {}).get('answer', None)
                question_type = detailed_questions.get(question_id, {}).get('question_type', None)

                if user_answer and check_answer(user_answer, correct_answer, question_type):
                    score += 1

            percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0
            print(f"Your score for {section}: {percentage_score:.2f}%")

            # Insert results into the database
            cursor.execute("""
                INSERT INTO results (student_number, exam_attempt, subject, score, true_count, false_count)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user.student_number, attempts + 1, section, percentage_score, score, total_questions - score))

            conn.commit()

        # Update user attempts AFTER successful exam completion
        cursor.execute("""
            UPDATE users
            SET attempts = attempts + 1
            WHERE student_number = %s
        """, (user.student_number,))
        conn.commit()

        print("Exam results recorded successfully.")

    except psycopg2.Error as e:
        print(f"Error during exam process: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("Database connection closed.")


def show_exam_results(user, db_config):
    """
    Display exam results for the user based on their role.
    If the user is a student, their own results are displayed.
    If the user is a teacher, they can view results of any student.
    
    :param user: User object containing user details.
    :param db_config: Dictionary containing the database configuration.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        if user.role[0] == "s":  # Student role
            user_id = user.student_number
            cursor.execute("""
                SELECT id, exam_attempt, subject, score, true_count, false_count
                FROM results
                WHERE student_number = %s
            """, (user_id,))
            user_data = cursor.fetchall()

            if not user_data:
                print("No exam results found for this user.")
                return

            print("\n=== Your Exam Results ===")
            for result in user_data:
                result_id, attempt_num, subject, score, true_count, false_count = result
                print(f"\nAttempt {attempt_num} - Subject: {subject.capitalize()}")
                print(f"Score: {score:.2f}%")
                print(f"Correct: {true_count}, Incorrect: {false_count}")
                print("-" * 40)

        elif user.role[0] == "t":  # Teacher role
            student_id = input("Enter the student ID: ").strip()

            # Query for student's results
            cursor.execute("""
                SELECT id, exam_attempt, subject, score, true_count, false_count
                FROM results
                WHERE student_number = %s
            """, (student_id,))
            student_data = cursor.fetchall()

            if not student_data:
                print(f"No exam results found for student ID: {student_id}. Please check the ID.")
                return

            teacher_subject = user.subject

            print(f"\n=== Exam Results for Student ID: {student_id} ===")
            print(f"Teacher's Subject: {teacher_subject}")

            for result in student_data:
                result_id, attempt_num, subject, score, true_count, false_count = result
                if subject.lower() == teacher_subject.lower():
                    print(f"\nAttempt {attempt_num} - Subject: {subject.capitalize()}")
                    print(f"Score: {score:.2f}%")
                    print(f"Correct: {true_count}, Incorrect: {false_count}")
                    print("-" * 40)

        else:
            print("Access denied. Invalid user role.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def show_school_class_results(user, db_config):
    """
    Display exam results for students in a specific school and class, filtered by the teacher's subject.
    Only accessible by teachers.
    
    :param user: User object containing user details.
    :param db_config: Dictionary containing the database configuration.
    """
    if user.role[0] != "t":
        print("Access denied. Only teachers can view this information.")
        return
    
    school_id = input("Enter the school ID: ").strip()
    class_number = input("Enter the class number (e.g., '8-B'): ").strip()

    try:
        # Connect to the database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Query students based on school and class
        cursor.execute("""
        SELECT 
            users.student_number, 
            users.username, 
            results.exam_attempt, 
            results.subject, 
            results.score, 
            results.true_count, 
            results.false_count
        FROM results
        INNER JOIN users 
        ON results.student_number = users.student_number 
        WHERE users.school_name = %s AND users.class_number = %s AND users.role = 'student'
        """, (school_id, class_number))

        students = cursor.fetchall()
        
        if not students:
            print("No students found for this school and class.")
            return

        print(f"\nExam results for School: {school_id}, Class: {class_number}")

        # Filter by teacher's subject
        teacher_subject = user.subject.lower()
        filtered_students = []

        for student in students:
            student_number, username, exam_attempt, subject, score, true_count, false_count = student

            # Match results by teacher's subject
            if subject.lower() == teacher_subject:
                filtered_students.append((student_number, username, exam_attempt, subject, score, true_count, false_count))

        if not filtered_students:
            print(f"No students found with results for subject: {teacher_subject}.")
            return

        # Display results for filtered students
        for student_number, username, exam_attempt, subject, score, true_count, false_count in filtered_students:
            print(f"\nResults for {username} (ID: {student_number}):")
            print(f"Attempt {exam_attempt} - Subject: {subject.capitalize()}")
            print(f"Score: {score:.2f}%")
            print(f"Correct: {true_count}, Incorrect: {false_count}")
            print("-" * 40)

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()


def admin_menu(user, db_config):
    """
    Menu for admins to manage the system.
    """
    while True:
        print("\n--- Admin Menu ---")
        print(f"Welcome, {user.username}. You have full access to system management.")
        print("1. Add User")
        print("2. List Users")
        print("3. Update User")
        print("4. Delete User")
        print("5. View All Passwords")
        print("6. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_user()
        elif choice == "2":
            print("\n--- User List ---")
            print("1. All Users")
            print("2. Students")
            print("3. Teachers")
            role_choice = input("Select a user type: ").strip()
            
            role_map = {
                "1": None,
                "2": "student", 
                "3": "teacher"
            }
            
            selected_role = role_map.get(role_choice)
            users = user.list_users(selected_role)
            if not users:
                print("No users found.")
            else:
                print("\n--- User Details ---")
                for u in users:
                    print(f"ID: {u['id']:<8}, Name: {u['username']:<10}, Role: {u['role']:<8}")
            
            input("\nPress Enter to return to the menu.")  # Wait before returning to menu

        elif choice == "3":
            user_id = input("Enter user ID to update: ").strip()
            user.update_user(user_id)
        
        elif choice == "4":
            user.delete_user()
        elif choice == "5":
            user.list_passwords()   
        
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")



def teacher_menu(user, db_config):
    print("\n--- Teacher Menu ---")
    
    while True:
        print("\n=== Teacher Menu ===")
        print("1. View Exam Results for Students")
        print("2. View School and Class Results")
        print("3. Add, Update, or Delete Questions")
        print("4. Logout")

        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            show_exam_results(user, db_config) 
        elif choice == "2":
            show_school_class_results(user, db_config) 
        elif choice == "3":
            question_bank = QuestionBank(db_config)  # Create QuestionBank instance with db_config
            question_bank.question_menu() 
        elif choice == "4":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")

def student_menu(user, db_config):
    """
    Menu for student to view their own results and take exams.
    """
    while True:
        print("\n=== Student Menu ===")
        print("1. View Exam Results")
        print("2. Take an Exam")
        print("3. Logout")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            show_exam_results(user, db_config)
        elif choice == "2":
            take_exam(user, db_config)
        elif choice == "3":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")