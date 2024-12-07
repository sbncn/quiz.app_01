from tools.user import User, hash_password
from tools.timer import Timer
from tools.questions import Question
from tools.question_bank import QuestionBank
from tools.exam import Exam
import json
import random


def generate_unique_id(users_data, role):
    """
    Generates a unique ID based on the role (student or teacher).
    """
    prefix = "S" if role == "student" else "T"
    while True:
        new_id = f"{prefix}{random.randint(1000, 9999)}"
        if all(
            user_data.get("student_number") != new_id and 
            user_data.get("teacher_id") != new_id 
            for user_data in users_data.values()
            ):
            return new_id
     

def signup():
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users_data = {}

    print("\n--- Add New User ---")
    username = input("Enter username: ").strip()
    surname = input("Enter surname: ").strip()
    password = input("Enter password: ").strip()
    role = input("Enter role (student/teacher): ").strip().lower()

    if role not in ["student", "teacher"]:
        print("Invalid role. Please choose 'student' or 'teacher'.")
        return

    # Kullanıcıya özgü ID üretimi
    unique_id = generate_unique_id(users_data, role)

    # Kullanıcıdan role göre ek bilgiler al
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

    # Admin olup olmadığını belirle
    is_admin = input("Is this user an admin? (yes/no): ").strip().lower() == "yes"

    # Yeni kullanıcı oluşturma
    user = User(
        admin=is_admin,
        username=username,
        surname=surname,
        student_number=student_number,
        teacher_id=teacher_id,
        password=password,
        role=role,
        subject=subject,
        school_name=school_name,
        class_number=class_number
    )

    # JSON dosyasına eklemek için kullanıcı verisini hazırlama
    users_data[unique_id] = {
        "username": user.username,
        "surname": user.surname,
        "password": user.password,
        "student_number": user.student_number,
        "teacher_id": user.teacher_id,
        "role": user.role,
        "subject": user.subject,
        "school_name": user.school_name,
        "class_number": user.class_number,
        "admin": user.admin,
        "attempts": user.attempts,
        "score": user.score,
        "max_attempts": user.max_attempts,
        "success_per_section": user.success_per_section
    }

    # Veriyi JSON dosyasına yaz
    try:
        with open("user/users.json", "w") as f:
            json.dump(users_data, f, indent=4)
        print(f"User '{username} {surname}' with ID '{unique_id}' has been created.")
    except Exception as e:
        print(f"Error saving user: {e}")
    

def login():
    print("\n--- Login ---")
    user_id = input("Enter your:\nStudent Number\nTeacher ID\nAdmin ID\n: ").strip()

    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No users found. Please sign up first.")
        return None
    
    user_data = None
    username = None
    for uname, data in users_data.items():
        if (
            data.get("student_number") == user_id 
            or data.get("teacher_id") == user_id 
            or data.get ("admin_id")== user_id
            ):
            user_data = data
            username = uname
            break
      
    if not user_data:
        print("User not found. Please sign up first.")
        return None

    
    user = User(
        username,
        user_data['username'],
        user_data['surname'],
        user_data.get('student_number'),
        user_data.get('password'),
        user_data.get('teacher_id'),
        user_data.get('role'),
        user_data.get('subject'),
        user_data.get('admin_id')
    )
    
    print(f"Welcome {user_data['username']} ({user_data.get("role").capitalize()}).")
    
    if not user.has_attempts_left():
        print("You have exceeded the maximum number of login attempts. Please try again later.")
        return None
    
    user.increment_attempts()
    password_try = 0
    while password_try < 3:
        password = input("Enter your password: ").strip()
        hashed_input_password = hash_password(password)

        if hashed_input_password == user_data['password']:
            print("Login successful.")
            # Redirect to the appropriate menu based on the role
            if user_data.get("role") == "teacher":
                show_teacher_menu(user)
            elif user_data.get("role") == "student":
                show_student_menu(user)

            elif user_data.get("role") == "admin":  # Admin için yönlendirme
                show_admin_menu(user)
            return user
            ...
            if user_data.get("role") == "teacher":
                show_teacher_menu(user)
            else:
                show_student_menu(user)
            return user
            ...
        else:
            print("Incorrect password. Try again.")
            password_try += 1
    
    print("Too many failed login attempts.")
    return None
    
def show_exam_results(user):  # for student menu
    """
    Display exam results for the user.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
        
        user_data = users_data.get(user.username, {})
        if 'exam_results' not in user_data:
            print("No exam results found for this user.")
            return
        
        print("\n=== Your Exam Results ===")
        
        
        for attempt_num, result in enumerate(user_data.get('exam_results', []), 1):
            print(f"\nAttempt {attempt_num}:")
            total_score = 0
            # Her bölüm için doğru ve yanlış cevapları yazdır
            
            for section, section_data in result.items():
                if section != 'overall_score':
                    #print(f"Section {section[-1]}: {score:.2f}/100")
           # print(f"Overall Score: {results.get('overall_score', 0):.2f}%")
            #print("Status:", "PASSED" if results.get('overall_score', 0) >= 75 else "FAILED")
            #print("-" * 40)
                    print(f"Section {section[-1]}: {section_data.get('score', 0):.2f}/100")
            print(f"Overall Score: {user_data.get('overall_score', 0):.2f}%")
            print("Status:", "PASSED" if user_data.get('overall_score', 0) >= 75 else "FAILED")
            print("-" * 40)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No exam results found.")

def take_exam(user):
    """
    Handle the exam taking process
    """
    # Check if user has remaining exam attempts
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
            exam_attempts = users_data.get(user.username, {}).get('exam_attempts', 0)
            
        if exam_attempts >= 2:
            print("You have no remaining exam attempts. Maximum attempts (2) reached.")
            return
    except (FileNotFoundError, json.JSONDecodeError):
        exam_attempts = 0

    print(f"\nStarting exam (Attempt {exam_attempts + 1}/2)")
    
    time_limit = 1800  # 30 minutes
    timer = Timer(time_limit)
    timer.start_timer()
    
    total_score = 0
    exam_finished = False
    exam_results = {}

    for section in range(1, 5):
        print(f"...........................................................................\n--- Starting Section {section} ---")
        question = Question(section)
        correct_answers = 0
        total_questions = 5
        answers_given = []  # Store student's answers

        for _ in range(total_questions):
            if not timer.check_time():
                print("\nTime's up! Ending the exam.")
                exam_finished = True        
                break

            remaining_time = timer.get_remaining_time()
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            print(f"Remaining time: {minutes} minutes {seconds} seconds")

            score = question.ask_question()
            correct_answers += (score / question.question_score)
            answers_given.append(score)  # Store answer

        section_score = (correct_answers / total_questions) * 100
        exam_results[f"section{section}"] = section_score
        total_score += section_score
        false_answers = total_questions - correct_answers

        # Save section results
        exam_results[f"section{section}"] = {
            "score": section_score,
            "true_count": correct_answers,
            "false_count": false_answers,
            "answers": answers_given } # Store the list of answers for review

        print(f"Section {section} completed. Total Question: {total_questions} \nCorrect Answers: {correct_answers}, False Answers: {false_answers} \nScore: {section_score:.2f}/100")
        if exam_finished:
            break

    overall_score = total_score / len(exam_results)
    exam_results['overall_score'] = overall_score

    # Update user data with exam results
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
        
        if user.username not in users_data:
            users_data[user.username] = {}
        
        if 'exam_results' not in users_data[user.username]:
            users_data[user.username]['exam_results'] = []
        
        users_data[user.username]['exam_results'].append(exam_results)
        users_data[user.username]['exam_attempts'] = exam_attempts + 1
        
        with open("user/users.json", "w") as f:
            json.dump(users_data, f, indent=4)
            
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error saving exam results.")

    print(f"\n--- Exam Completed ---")
    print(f"Your overall score: {overall_score:.2f}%")
    print("Status:", "PASSED" if overall_score >= 75 else "FAILED")
    


def show_student_exam_results(user):
    
    if user.role[0] != "T":
        print("Access denied. Only teachers can view this information.")
        return
    
    student_id = input("Enter the student ID: ").strip()
    
    # Kullanıcı dosyasından öğrenciyi bul
    with open('user/users.json', 'r') as f:
        users = json.load(f)
    
    student = next(
            (
                u for u in users.values()
                if "student_number" in u and "role" in u and u["student_number"] == student_id and u["role"] == "student"
            ),
            None
    )

    if not student:
        print("Student not found.")
        return
    
    print(f"\nExam results for {student['username']} (ID: {student['student_number']}):")
    for result in student.get("exam_results", []):
        # Get the score for each section
        section1_score = result.get('section1', {}).get('score', 0.0)
        section2_score = result.get('section2', {}).get('score', 0.0)
        section3_score = result.get('section3', {}).get('score', 0.0)
        section4_score = result.get('section4', {}).get('score', 0.0)

        # Get the true/false counts for each section
        section1_true = result.get('section1', {}).get('true_count', 0.0)
        section1_false = result.get('section1', {}).get('false_count', 0.0)
        section2_true = result.get('section2', {}).get('true_count', 0.0)
        section2_false = result.get('section2', {}).get('false_count', 0.0)
        section3_true = result.get('section3', {}).get('true_count', 0.0)
        section3_false = result.get('section3', {}).get('false_count', 0.0)
        section4_true = result.get('section4', {}).get('true_count', 0.0)
        section4_false = result.get('section4', {}).get('false_count', 0.0)

        # Print the scores and true/false counts for each section
        print(f"  - Section 1: Score: {section1_score}, T: {section1_true}, F: {section1_false}")
        print(f"  - Section 2: Score: {section2_score}, T: {section2_true}, F: {section2_false}")
        print(f"  - Section 3: Score: {section3_score}, T: {section3_true}, F: {section3_false}")
        print(f"  - Section 4: Score: {section4_score}, T: {section4_true}, F: {section4_false}")

        # print(f"- Section Scores: {section1_score}, {section2_score}, {section3_score}, {section4_score}")
        print(f"- Overall Score: {result.get('overall_score', 0.0)}")



def show_school_class_results(user):    # for teacher menu
    # "user" bir User sınıfı nesnesi, bu yüzden ["role"] yerine ".role" kullanmalıyız
    if user.role[0] != "T":
        print("Access denied. Only teachers can view this information.")
        return
    
    school_id = input("Enter the school ID: ").strip()
    class_number = input("Enter the class number (e.g., '8-B'): ").strip()
    
    with open('user/users.json', 'r') as f:
        users = json.load(f)
    
    # Filter students by school_id and class_number
    students = [u for u in users.values() if u.get("school_name") == school_id and u.get("class_number") == class_number and u.get("role") == "student"]
    
    if not students:
        print("No students found for this school and class.")
        return
    
    print(f"\nExam results for School: {school_id}, Class: {class_number}")


    # for student in students:
        # Print student's basic information
        
    # Aggregating data
    class_results = {}
    for student in students:
        class_id = student['class_number']
        if class_id not in class_results:
            class_results[class_id] = {'overall_score': 0, 'true_count': 0, 'false_count': 0, 'student_count': 0}   
        
        # Iterate over the student's exam results and print them
        for result in student.get("exam_results", []):
            print(f"  - Section Scores: {result.get('section1', 0.0)}, {result.get('section2', 0.0)}, {result.get('section3', 0.0)}, {result.get('section4', 0.0)}")
            print(f"  - Overall Score: {result.get('overall_score', 0.0)}")
    
    show_teacher_menu(user)



    while True:
        print("\n--- Admin Menu ---")
        print(f"Welcome, {user.username}. You have full access to system management.")
        print("1. Add Users")
        print("2. View Student Passwords")
        print("3. View Teacher Passwords")
        print("4. Edit Users")
        print("5. Delete Users")


        print("6. Exit")
        
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print("Add users... (this is a placeholder)")
            # add users
        elif choice == "2":
            print("View Student Passwords... (this is a placeholder)")
            # Student passwords
        elif choice == "3":
            print("View Teacher Passwords...(this is a placeholder)")
        elif choice == "4":
             print("4. Edit Users...(this is a placeholder)")
        elif choice == "5":
            delete_user(self)
            print("5. Delete Users...(this is a placeholder)")
        elif choice =="6":     
            break  # Döngüyü kırarak admin menüsünden çık
        else:
            print("Invalid choice. Please try again.")


def show_teacher_menu(user):
    """
    Display the main menu for teachers.
    """
    
    while True:
        print("\n=== Teacher Menu ===")
        print("1. View Exam Results for Students")
        print("2. View School and Class Results")
        print("3. Add, Update, or Delete Questions")  
        print("4. Logout")
        
        choice = input("Choose an option (1-4): ").strip()
        question_bank = QuestionBank('questions')  # Base path to the questions directory
        
        if choice == "1":
            show_student_exam_results(user) # Öğretmen için ek özellikler burada eklenebilir
        elif choice == "2":
            show_school_class_results(user)  # Yeni fonksiyon çağrılır
        elif choice == "3":
            question_bank.question_menu()
        elif choice == "4":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")

def show_student_menu(user):
    """
    Display the main menu after login
    """
    
    while True:
        print("\n=== Main Menu ===")
        print("1. View Exam Results")
        print("2. Take New Exam")
        print("3. Logout")
        
        choice = input("Choose an option (1-3): ").strip()
        
        if choice == "1":
            show_exam_results(user)
        elif choice == "2":
            take_exam(user)
        elif choice == "3":
            print("Logging out...")
            break
        else:

            print("Invalid choice. Please try again.")

def show_admin_menu(user):
    while True:
        print("\n--- Admin Menu ---")
        print(f"Welcome, {user.username}. You have full access to system management.")
        print("1. Add User")
        print("2. List Users")
        print("3. Update User")
        print("4. Delete User")
        print("5.  View All Passwords")
        print("6. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            # Mevcut signup fonksiyonunu kullan
            signup()
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
                print(f"ID: {u['id']:<8}, Name: {u['username']:<10},Role: {u['role']:<8}")
                #print(f"{u['id']:<10} {u['username']:<20} {u['role']:<15}")
    
            input("\nPress Enter to return to the menu.")  # Menüye dönmeden önce bekleme

        elif choice == "3":
            user_id = input("Enter user ID to update: ").strip()
            user.update_user(user_id)
        
        elif choice == "4":
            user.delete_user()
        elif choice == "5" :
            user.list_passwords()   
        
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")



def start_menu():
    #ensure_admin_exists(self)  # Admin hesabı kontrolü
    while True:
        print("\n--- Welcome to the Exam System ---")
        print("1. Login")
        print("2. Sign Up")
        print("3. Exit")

        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            login()
        elif choice == "2":
            signup()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    start_menu()