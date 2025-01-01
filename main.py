from tools.user import User
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
        print("No users found. Please sign up first.1")
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
        print("User not found. Please sign up first.2")
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
        user_data.get('admin_id'),
        user_data.get("score")
    )
    
    print(f"Welcome {user_data['username']} ({user_data.get('role').capitalize()}).")
    
    if not user.has_attempts_left():
        print("You have exceeded the maximum number of login attempts. Please try again later.")
        return None
    
    user.increment_attempts()
    password_try = 0
    while password_try < 3:
        password = input("Enter your password: ").strip()
        if user_data.get("role") == "teacher":
                show_teacher_menu(user)
        elif user_data.get("role") == "student":
                show_student_menu(user)
        elif user_data.get("role") == "admin":  # Admin için yönlendirme
                show_admin_menu(user)
        return user
    print("Too many failed login attempts.")
    return None
    

def take_exam(user):
    # Kullanıcı sınav denemelerini kontrol et
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
    time_limit = 1800  # 30 dakika
    timer = Timer(time_limit)
    timer.start_timer()
    
    total_score = 0
    exam_finished = False
    exam_results = {}

    # Bölüm isimleri, her bölüm için tanımlı
    section_names = ["English", "Computer", "History", "Geography"]

    # Her bölüm için soruları al ve sınavı başlat
    for section_idx, section_name in enumerate(section_names, start=1):
        print(f"...........................................................................\n--- Starting {section_name} Section ---")
        question = Question(section_idx)  # Her bölüm için Question sınıfını kullan
        correct_answers = 0
        total_questions = 5
        answers_given = []  # Öğrencinin verdiği cevapları saklayacağız
        
        for _ in range(total_questions):
            if not timer.check_time():
                print("\nTime's up! Ending the exam.")
                exam_finished = True
                break
            
            # Kalan zamanı göster
            remaining_time = timer.get_remaining_time()
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            print(f"Remaining time: {minutes} minutes {seconds} seconds")
            
            # Soruyu sor ve cevabını al
            score = question.ask_question()  # Soruyu sormak ve cevabı almak
            correct_answers += (score / question.question_score)
            answers_given.append(score)  # Verilen cevabı sakla
        
        # Bölüm skoru hesapla
        section_score = (correct_answers / total_questions) * 100
        exam_results[f"{section_name}_score"] = {
            "score": section_score,
            "true_count": correct_answers,
            "false_count": total_questions - correct_answers,
            "answers": answers_given  # Verilen cevapları sakla
        }
        
        total_score += section_score
        print(f"{section_name} Section completed. Total Questions: {total_questions} \nCorrect Answers: {correct_answers}, False Answers: {total_questions - correct_answers} \nScore: {section_score:.2f}/100")
        
        if exam_finished:
            break
    
    # Genel sınav skoru
    overall_score = total_score / len(exam_results)
    exam_results['overall_score'] = overall_score

    # Kullanıcı verilerini kaydetme (Sınav sonuçlarını ve denemeleri)
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
        
        user_id = user.student_number if user.student_number else user.teacher_id
        
        if user_id not in users_data:
            users_data[user_id] = {
                "exam_results": [],
                "exam_attempts": 0
            }
        
        if 'exam_results' not in users_data[user_id]:
            users_data[user_id]['exam_results'] = []

        users_data[user_id]['exam_results'].append(exam_results)
        users_data[user_id]['exam_attempts'] = exam_attempts + 1
        
        with open("user/users.json", "w") as f:
            json.dump(users_data, f, indent=4)
    
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error saving exam results.")

    # Sınav tamamlandığında sonuçları göster
    print(f"\n--- Exam Completed ---")
    print(f"Your overall score: {overall_score:.2f}%")
    print("Status:", "PASSED" if overall_score >= 75 else "FAILED")

def show_exam_results(user):
    """
    Display exam results for the user based on their role.
    If the user is a student, their own results are displayed.
    If the user is a teacher, they can view results of any student.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)

        if user.role[0] == "s":  # Student role
            user_data = users_data.get(user.student_number, None)
            if not user_data:
                print(f"No data found for student number: {user.student_number}. Please check the student number.")
                return

            if 'exam_results' not in user_data or not user_data['exam_results']:
                print("No exam results found for this user.")
                return

            print("\n=== Your Exam Results ===")

            # Section names dynamically detected if available
            section_names = [
                key.replace("_score", "") for key in user_data['exam_results'][0].keys() if key.endswith("_score")
            ]

            for attempt_num, result in enumerate(user_data.get('exam_results', []), 1):
                print(f"\nAttempt {attempt_num}:")

                # Print results for each section
                for section_name in section_names:
                    section_data = result.get(f"{section_name}_score", 0)
                    if isinstance(section_data, dict):
                        print(f"{section_name}: {section_data.get('score', 0):.2f}")
                    else:
                        print(f"{section_name}: {section_data:.2f}")

                # Print overall score and status
                overall_score = result.get('overall_score', 0)
                print(f"Overall Score: {overall_score:.2f}%")
                print("Status:", "PASSED" if overall_score >= 75 else "FAILED")
                print("-" * 40)

        elif user.role[0] == "t":  # Teacher role
            student_id = input("Enter the student ID: ").strip()

            # Find student data
            student_data = users_data.get(student_id, None)
            if not student_data:
                print(f"No data found for student ID: {student_id}. Please check the ID.")
                return

            if 'exam_results' not in student_data or not student_data['exam_results']:
                print("No exam results found for this student.")
                return

            # Teacher's subject (branch)
            teacher_subject = user.subject

            print(f"\n=== Exam Results for Student ID: {student_id} ===")
            print(f"Teacher Subject: {teacher_subject}")
            
            # Section names dynamically detected if available
            section_names = [
                key.replace("_score", "") for key in student_data['exam_results'][0].keys() if key.endswith("_score")
            ]

            for attempt_num, result in enumerate(student_data.get('exam_results', []), 1):
                print(f"\nAttempt {attempt_num}:")

                # Print results for each section
                for section_name in section_names:
                    if section_name.lower() == teacher_subject.lower():  # Only display results for the teacher's subject  
                        section_data = result.get(f"{section_name}_score", 0)
                        if isinstance(section_data, dict):
                            print(f"{section_name}: {section_data.get('score', 0):.2f}")
                        else:
                            print(f"{section_name}: {section_data:.2f}")

                # Print overall score and status
                overall_score = result.get('overall_score', 0)
                print(f"Overall Score: {overall_score:.2f}%")
                print("Status:", "PASSED" if overall_score >= 75 else "FAILED")
                print("-" * 40)

        else:
            print("Access denied. Invalid user role.")

    except (FileNotFoundError, json.JSONDecodeError):
        print("Error reading user data. Please ensure the users.json file exists and is correctly formatted.")


def show_school_class_results(user):
    # "user" bir User sınıfı nesnesi, bu yüzden ["role"] yerine ".role" kullanmalıyız
    if user.role[0] != "t":
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
    
    # Filter students by subject
    teacher_subject = user.subject
    students = [
        s for s in students if any(
            f"{teacher_subject}_score" in result for result in s.get('exam_results', [])
        )
    ]
    
    if not students:
        print(f"No students found with results for subject: {teacher_subject}.")
        return
    
    # Print results for each student
    for student in students:
        print(f"\nResults for {student['username']} (ID: {student['student_number']}):")
        
        for attempt_num, result in enumerate(student.get('exam_results', []), 1):
            print(f"\nAttempt {attempt_num}:")
            
            # Print section results for the teacher's subject only
            for section_name in result.keys():
                if section_name.startswith(teacher_subject):
                    section_data = result.get(section_name, {})
                    print(f"  - {section_name.replace('_score', '')}: Score: {section_data.get('score', 0):.2f}, T: {section_data.get('true_count', 0)}, F: {section_data.get('false_count', 0)}")
            
            print(f"  - Overall Score: {result.get('overall_score', 0)}")
    
    show_teacher_menu(user)

def admin_menu(user):
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
            add_user()  # Kullanıcı ekleme işlemi
        elif choice == "2":
            view_student_passwords()  # Öğrenci şifrelerini görme
        elif choice == "3":
            view_teacher_passwords()  # Öğretmen şifrelerini görme
        elif choice == "4":
            edit_user()  # Kullanıcı düzenleme
        elif choice == "5":
            delete_user()  # Kullanıcı silme
        elif choice == "6":
            break  # Döngüyü kırarak admin menüsünden çık
        else:
            print("Invalid choice. Please try again.")

def add_user():
    # Yeni kullanıcı eklemek için gerekli işlemleri burada yapabilirsiniz
    print("Adding a new user...")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    role = input("Enter role (student/teacher/admin): ").strip().lower()
    
    # User information can be saved to a file, database, etc.
    new_user = {
        "username": username,
        "password": password,
        "role": role
    }

    # Simulate saving the user to a database or a file
    print(f"User {username} added successfully with role {role}.")
    # Add the logic to actually save the user here (e.g., appending to a file)

def view_student_passwords():
    print("Viewing student passwords...")
    # Öğrenci şifrelerini göstermek için gerekli işlemler
    with open('user/users.json', 'r') as f:
        users = json.load(f)
    
    for user in users.values():
        if user["role"] == "student":
            print(f"Student: {user['username']}, Password: {user['password']}")

def view_teacher_passwords():
    print("Viewing teacher passwords...")
    # Öğretmen şifrelerini göstermek için gerekli işlemler
    with open('user/users.json', 'r') as f:
        users = json.load(f)
    
    for user in users.values():
        if user["role"] == "teacher":
            print(f"Teacher: {user['username']}, Password: {user['password']}")

def edit_user():
    print("Editing a user...")
    username_to_edit = input("Enter the username of the user to edit: ").strip()
    
    # Kullanıcıyı bulmak ve düzenlemek için işlemler
    with open('user/users.json', 'r') as f:
        users = json.load(f)
    
    user_to_edit = next((u for u in users.values() if u['username'] == username_to_edit), None)
    
    if not user_to_edit:
        print("User not found.")
        return
    
    # Düzenleme işlemi
    new_username = input(f"Enter new username (current: {user_to_edit['username']}): ").strip()
    new_password = input("Enter new password: ").strip()
    new_role = input(f"Enter new role (current: {user_to_edit['role']}): ").strip().lower()

    user_to_edit['username'] = new_username
    user_to_edit['password'] = new_password
    user_to_edit['role'] = new_role
    
    # Güncellenmiş veriyi dosyaya kaydet
    with open('user/users.json', 'w') as f:
        json.dump(users, f, indent=4)

    print(f"User {username_to_edit} updated successfully.")

def delete_user():
    print("Deleting a user...")
    username_to_delete = input("Enter the username of the user to delete: ").strip()

    # Kullanıcıyı bulmak ve silmek için işlemler
    with open('user/users.json', 'r') as f:
        users = json.load(f)
    
    user_to_delete = next((u for u in users.values() if u['username'] == username_to_delete), None)

    if not user_to_delete:
        print("User not found.")
        return
    
    # Kullanıcıyı sil
    users = {k: v for k, v in users.items() if v['username'] != username_to_delete}
    
    # Güncellenmiş veriyi dosyaya kaydet
    with open('user/users.json', 'w') as f:
        json.dump(users, f, indent=4)

    print(f"User {username_to_delete} deleted successfully.")


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
            show_exam_results(user) # Öğretmen için ek özellikler burada eklenebilir
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
        print("5. View All Passwords")
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