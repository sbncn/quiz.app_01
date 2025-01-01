from tools.user import User
from tools.timer import Timer
from tools.questions import Question
from tools.question_bank import QuestionBank
from tools.exam import Exam
import json
import random
from tools.user import hash_password
from tools.user import is_username_unique



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
    name = input("Enter first name: ").strip()
    surname = input("Enter surname: ").strip()
    username = input("Enter a unique username: ").strip()

    # Kullanıcı adı benzersizlik kontrolü
    while not is_username_unique(users_data, username):
        print("This username is already taken. Please choose another one.")
        username = input("Enter a unique username: ").strip()

    role = input("Enter role (student/teacher): ").strip().lower()
    if role not in ["student", "teacher"]:
        print("Invalid role. Please choose 'student' or 'teacher'.")
        return

    password = input("Enter password: ").strip()
    user_id = generate_unique_id(users_data, role)

    # Ek alanlar
    email = input("Enter email: ").strip()
    phone_number = input("Enter phone number: ").strip()
    address = input("Enter address: ").strip()

    if role == "student":
        school_name = input("Enter school name: ").strip()
        class_number = input("Enter class number: ").strip()
        teacher_id = None
        subject = None
    elif role == "teacher":
        subject = input("Enter subject: ").strip()
        school_name = None
        class_number = None
        teacher_id = user_id

    is_admin = input("Is this user an admin? (yes/no): ").strip().lower() == "yes"

    # Kullanıcı nesnesi oluşturma
    user = User(
        admin=is_admin,
        username=username,
        name=name,
        surname=surname,
        password=password,
        student_number=user_id if role == "student" else None,
        teacher_id=teacher_id,
        role=role,
        subject=subject,
        school_name=school_name,
        class_number=class_number
    )

    # Kullanıcı verilerini JSON formatına dönüştürme
    users_data[user_id] = {
        "user_id": user_id,
        "username": user.username,
        "name": user.name,
        "surname": user.surname,
        "password": user.password,
        "role": user.role,
        "email": email,
        "phone_number": phone_number,
        "address": address,
        "school_name": user.school_name,
        "class_number": user.class_number,
        "subject": user.subject,
        "admin": user.admin,
        "attempts": user.attempts,
        "score": user.score,
        "max_attempts": user.max_attempts,
        "success_per_section": user.success_per_section
    }

    # Veriyi JSON dosyasına kaydetme
    try:
        with open("user/users.json", "w") as f:
            json.dump(users_data, f, indent=4)
        print(f"User '{name} {surname}' with username '{username}' and ID '{user_id}' has been created.")
    except Exception as e:
        print(f"Error saving user: {e}")

def login():
    """
    Kullanıcı girişi için login işlevi.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No users found. Please sign up first.")
        return None

    username = input("Enter your username: ").strip()

    # Kullanıcıyı username ile bulma
    user_data = None
    user_id = None
    for uid, data in users_data.items():
        if data["username"] == username:
            user_data = data
            user_id = uid
            break

    if not user_data:
        print("User not found. Please sign up first.")
        return None

    for attempt in range(3):  # Kullanıcıya 3 deneme hakkı tanı
        password = input("Enter your password: ").strip()
        if user_data["password"] == hash_password(password):
            print(f"Welcome, {user_data['name']} {user_data['surname']}!")
            #return user_id

            # Kullanıcı rolüne göre menü göster
            if user_data["role"] == "student":
                show_student_menu(user_id)
            elif user_data["role"] == "teacher":
                show_teacher_menu(user_id)
            elif user_data["role"] == "admin":
                show_admin_menu(user_id)
            else:
                print("Invalid role. Access denied.")
            return user_id

        print(f"Incorrect password. {2 - attempt} attempts left.")
    print("Too many failed attempts. Try again later.")
    return None


    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("No users found. Please sign up first.")
        return None

    username = input("Enter your username: ").strip()

    # Kullanıcıyı username ile bulma
    user_data = None
    user_id = None
    for uid, data in users_data.items():
        if data["username"] == username:
            user_data = data
            user_id = uid
            break

    if not user_data:
        print("User not found. Please sign up first.")
        return None

    for attempt in range(3):  # Kullanıcıya 3 deneme hakkı tanı
        password = input("Enter your password: ").strip()
        if user_data["password"] == hash_password(password):
            print(f"Welcome, {user_data['name']} {user_data['surname']}!")
            return user_id  # Giriş yapıldıktan sonra `user_id` döndürülür

        print(f"Incorrect password. {2 - attempt} attempts left.")
    print("Too many failed attempts. Try again later.")
    return None

def show_user_profile(user_id):
    """
    Kullanıcı profilini user_id ile gösterir.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
        user_data = users_data.get(user_id)

        if not user_data:
            print("User not found.")
            return

        print("\n--- User Profile ---")
        print(f"Name: {user_data['name']} {user_data['surname']}")
        print(f"Username: {user_data['username']}")
        print(f"Role: {user_data['role'].capitalize()}")
        print(f"Email: {user_data['email']}")
        print(f"Phone: {user_data['phone_number']}")
        print(f"Address: {user_data['address']}")
        print(f"School: {user_data.get('school_name', 'N/A')}")
        print(f"Class: {user_data.get('class_number', 'N/A')}")
        print(f"Subject: {user_data.get('subject', 'N/A')}")
        print(f"Admin: {'Yes' if user_data['admin'] else 'No'}")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error loading user data.")



    """
    Sınavı başlatır ve kullanıcıyı yönlendirir.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error loading user data.")
        return

    # Kullanıcı verisini kontrol et
    if user_data.get("exam_attempts", 0) >= 2:
        print("You have no remaining exam attempts. Maximum attempts (2) reached.")
        return

    print("\n--- Starting Exam ---")
    time_limit = 1800  # 30 dakika
    timer = Timer(time_limit)
    timer.start_timer()

    total_score = 0
    exam_results = {}

    # Bölüm isimleri
    section_names = ["English", "Computer", "History", "Geography"]

    for section_idx, section_name in enumerate(section_names, start=1):
        print(f"\n--- {section_name} Section ---")
        question = Question(section_idx)
        correct_answers = 0
        total_questions = 5

        for _ in range(total_questions):
            if not timer.check_time():
                print("\nTime's up! Ending the exam.")
                break

            score = question.ask_question()
            correct_answers += score / question.question_score

        # Bölüm skoru
        section_score = (correct_answers / total_questions) * 100
        exam_results[f"{section_name}_score"] = section_score
        total_score += section_score

    # Genel sınav skoru
    overall_score = total_score / len(section_names)
    exam_results["overall_score"] = overall_score

    print(f"\n--- Exam Completed ---")
    print(f"Your overall score: {overall_score:.2f}")
    print("Status:", "PASSED" if overall_score >= 75 else "FAILED")

    # Kullanıcı verilerini güncelle
    user_data["exam_attempts"] = user_data.get("exam_attempts", 0) + 1
    if "exam_results" not in user_data:
        user_data["exam_results"] = []
    user_data["exam_results"].append(exam_results)

    # Kullanıcı ID'si ile veriyi güncelle
    user_id = user_data.get("student_number") or user_data.get("teacher_id") or user_data.get("user_id")
    if not user_id:
        print("Error: Could not determine user ID.")
        return

    users_data[user_id] = user_data

    with open("user/users.json", "w") as f:
        json.dump(users_data, f, indent=4)

def take_exam(user_data):
    """
    Sınavı başlatır ve kullanıcıyı yönlendirir.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error loading user data.")
        return

    # Kullanıcı verisini kontrol et
    if user_data.get("exam_attempts", 0) >= 2:
        print("You have no remaining exam attempts. Maximum attempts (2) reached.")
        return

    print("\n--- Starting Exam ---")
    time_limit = 1800  # 30 dakika
    timer = Timer(time_limit)
    timer.start_timer()

    total_score = 0
    exam_results = {}

    # Bölüm isimleri
    section_names = ["English", "Computer", "History", "Geography"]

    for section_idx, section_name in enumerate(section_names, start=1):
        print(f"\n--- {section_name} Section ---")
        question = Question(section_idx)

        correct_answers = 0
        false_answers = 0
        total_questions = 5
        answers_given = []  # Verilen cevapların skorları burada tutulur

        for _ in range(total_questions):
            if not timer.check_time():
                print("\nTime's up! Ending the exam.")
                break

            # Soruyu sor ve cevabını al
            score = question.ask_question()
            if score > 0:
                correct_answers += 1
            else:
                false_answers += 1
            answers_given.append(score)  # Sorunun skoru (doğruysa puanı, yanlışsa 0)

        # Bölüm skoru
        section_score = (correct_answers / total_questions) * 100
        exam_results[f"{section_name}_score"] = section_score
        exam_results[section_name] = {
            "score": section_score,
            "true_count": correct_answers,
            "false_count": false_answers,
            "answers": answers_given
        }
        total_score += section_score

    # Genel sınav skoru
    overall_score = total_score / len(section_names)
    exam_results["overall_score"] = overall_score

    print(f"\n--- Exam Completed ---")
    print(f"Your overall score: {overall_score:.2f}")
    print("Status:", "PASSED" if overall_score >= 75 else "FAILED")

    # Kullanıcı verilerini güncelle
    user_data["exam_attempts"] = user_data.get("exam_attempts", 0) + 1
    if "exam_results" not in user_data:
        user_data["exam_results"] = []
    user_data["exam_results"].append(exam_results)

    user_id = user_data.get("student_number") or user_data.get("teacher_id") or user_data.get("user_id")
    if not user_id:
        print("Error: Could not determine user ID.")
        return

    users_data[user_id] = user_data

    with open("user/users.json", "w") as f:
        json.dump(users_data, f, indent=4)
        
def show_exam_results(user_id):
    """
    Kullanıcı sınav sonuçlarını user_id ile görüntüler.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)

        user_data = users_data.get(user_id)
        if not user_data:
            print("User not found.")
            return

        print(f"\n=== Exam Results for {user_data['name']} {user_data['surname']} ===")
        if user_data["role"] == "student":
            if 'exam_results' not in user_data or not user_data['exam_results']:
                print("No exam results found for this user.")
                return

            for attempt, result in enumerate(user_data["exam_results"], 1):
                print(f"\nAttempt {attempt}:")

                # Bölüm skorlarını ve detaylarını yazdır
                for section, section_result in result.items():
                    if section == "overall_score":
                        print(f"Overall Score: {section_result:.2f}")
                        print("Status:", "PASSED" if section_result >= 75 else "FAILED")
                    elif isinstance(section_result, dict):
                        # Detaylı bilgi formatında yazdır
                        print(f"{section}: {section_result['score']:.2f}/100")
                        print(f"  - True Answers: {section_result['true_count']}")
                        print(f"  - False Answers: {section_result['false_count']}")
                        print(f"  - Answers Given: {section_result['answers']}")
                    else:
                        # Bölüm skoru formatında yazdır
                        print(f"{section}: {section_result:.2f}/100")
        else:
            print("Access denied for this role.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error reading user data.")


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
def show_student_menu(user_id):
    """
    Öğrenci menüsünü gösterir.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)

        # Kullanıcı verisini user_id üzerinden alın
        user_data = users_data.get(user_id)
        if not user_data or user_data["role"] != "student":
            print("Access denied.")
            return

        print(f"\nWelcome {user_data['name']} {user_data['surname']}!")
        while True:
            print("\n=== Student Menu ===")
            print("1. View Exam Results")
            print("2. Take New Exam")
            print("3. Logout")

            choice = input("Choose an option (1-3): ").strip()

            if choice == "1":
                show_exam_results(user_id)
            elif choice == "2":
                take_exam(user_data)  # user_data geçiriliyor
            elif choice == "3":
                print("Logging out...")
                break
            else:
                print("Invalid choice. Please try again.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error loading user data.")
'''
def show_student_menu(user_id):
    """
    Öğrenci için ana menüyü göster.
    """
    try:
        with open("user/users.json", "r") as f:
            users_data = json.load(f)
        user_data = users_data.get(user_id)

        if not user_data:
            print("User not found.")
            return

        while True:
            print(f"\n=== Student Menu for {user_data['name']} {user_data['surname']} ===")
            print("1. View Exam Results")
            print("2. Take New Exam")
            print("3. Logout")

            choice = input("Choose an option (1-3): ").strip()

            if choice == "1":
                show_exam_results(user_id)
            elif choice == "2":
                take_exam(user_id)
            elif choice == "3":
                print("Logging out...")
                break
            else:
                print("Invalid choice. Please try again.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error loading user data.")
'''
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