import json
import hashlib
#import os

def hash_password(password):

    """Hash the password using SHA-256."""
    return hashlib.sha256(password.strip().encode('utf-8')).hexdigest()

class User:
    def __init__(self, admin, username, surname, student_number=None, teacher_id=None, password=None, role=None, subject=None, school_name=None, class_number=None):
        self.username = username
        self.surname = surname
        self.password = hash_password(password) if password else None
        self.student_number = student_number
        self.teacher_id = teacher_id
        self.role = role
        self.subject = subject
        self.school_name = school_name  
        self.class_number = class_number  
        self.attempts = 0
        self.score = 0
        self.max_attempts = 2
        self.success_per_section = {"section1": 0, "section2": 0, "section3": 0, "section4": 0}
        self.admin = admin

    def load_user_data(self):
        try:
            with open("user/users.json", "r") as f:
                users_data = json.load(f)

            if self.username in users_data:
                user_data = users_data[self.username]
                self.password = user_data['password']
                self.surname = user_data['surname']
                self.attempts = user_data['attempts']
                self.score = user_data['score']
                self.success_per_section = user_data['success_per_section']
                self.student_number = user_data['student_number']
                self.teacher_id = user_data.get('teacher_id')
                self.role = user_data.get('role')
                self.subject=user_data.get('subject')
                self.school_name = user_data.get('school_name')  # Yeni alan yükleniyor
                self.class_number = user_data.get('class_number')  # Yeni alan yükleniyor
            else:
                print(f"User '{self.username}' not found in the database. Adding user...")
                self.save_user_data(users_data)

        except FileNotFoundError:
            print("users/users.json file not found. Creating a new one.")
            self.save_user_data()
        except json.JSONDecodeError:
            print("The users.json file is empty or corrupted. Creating a new one.")
            self.save_user_data()

    # def save_user_data(self, users_data=None):
        if users_data is None:
            try:
                with open("user/users.json", "r") as f:
                    users_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                users_data = {}

        unique_id = self.student_number if self.student_number else self.teacher_id

        if self.teacher_id:  # Teacher
            users_data[unique_id] = {
                "username": self.username,
                "surname": self.surname,
                "teacher_id": self.teacher_id,
                "password": self.password,
                "role": self.role,
                "subject": self.subject
            }
        elif self.student_number:  # Student
            users_data[unique_id] = {
                "username": self.username,
                "surname": self.surname,
                "student_number": self.student_number,
                "password": self.password,
                "role": self.role,
                "school_name": self.school_name,  # Yeni alan kaydediliyor
                "class_number": self.class_number,  # Yeni alan kaydediliyor
                "attempts": self.attempts,
                "score": round(self.score, 2),
                "success_per_section": {
                    k: round(v, 2) for k, v in self.success_per_section.items()
                }
            }

        with open("user/users.json", "w") as f:
            json.dump(users_data, f, indent=4)

        print("Data to be written to file:", json.dumps(users_data, indent=4))

    def save_user_data(self, users_data=None):
        if users_data is None:
            try:
                with open("user/users.json", "r") as f:
                    users_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                users_data = {}

        unique_id = self.student_number if self.student_number else self.teacher_id

        if self.teacher_id:  # Teacher
            users_data[unique_id] = {
                "username": self.username,
                "surname": self.surname,
                "teacher_id": self.teacher_id,
                "password": self.password,
                "role": self.role,
                "subject": self.subject
            }
        elif self.student_number:  # Student
            users_data[unique_id] = {
                "username": self.username,
                "surname": self.surname,
                "student_number": self.student_number,
                "password": self.password,
                "role": self.role,  # Ensure role is added here
                "school_name": self.school_name,  # New field being saved
                "class_number": self.class_number,  # New field being saved
                "attempts": self.attempts,
                "score": round(self.score, 2),
                "success_per_section": {
                    k: round(v, 2) for k, v in self.success_per_section.items()
                }
            }

        with open("user/users.json", "w") as f:
            json.dump(users_data, f, indent=4)




    def delete_user(self):
        """ Delete a user from the system with error handling. """
        try:
            # Kullanıcı verilerini JSON dosyasından yükleme
            with open("user/users.json", "r") as f:
                users_data = json.load(f)
        except FileNotFoundError:
            print("Error: Users file not found.")
            return
        except json.JSONDecodeError:
            print("Error: Users file is corrupted or has invalid JSON format.")
            return
    
        if not users_data:
            print("No users found.")
            return

        try:
            print("Existing Users:")
            print(f"{'ID':<15} {'Name':<20} {'Role':<15}")
            print("-" * 50)
            for user_id, user in users_data.items():
                try:
                # Kullanıcı bilgilerini yazdır
                    print(f"{user_id:<15} {user['username']:<20} {user['role']:<15}")
                except KeyError as e:
                # Eksik anahtar varsa bilgilendir
                    print(f"Error: Missing key {e} for user ID {user_id}. Skipping this user.")
                    continue

        # Silinecek kullanıcı ID'sini al
            user_id_to_delete = input("Enter the ID of the user to delete: ").strip()
            if user_id_to_delete in users_data:
                del users_data[user_id_to_delete]
                try:
                # Güncellenmiş verileri dosyaya yaz
                    with open("user/users.json", "w") as f:
                        json.dump(users_data, f, indent=4)
                    print(f"User with ID {user_id_to_delete} has been deleted.")
                except IOError:
                    print("Error: Failed to save updated user data.")
            else:
                print("Error: User ID not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    
    def list_passwords(self):
        #"""Allow admin to view all user passwords."""
        if not self.admin:
            print("Access denied. Only admins can view passwords.")
            return

        try:
            with open("user/users.json", "r") as f:
                users_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("No users found.")
            return

        print("\n--- All User Passwords ---")
        for user_id, user_data in users_data.items():
            username = user_data.get("username", "N/A")
            role = user_data.get("role", "N/A")
            password = user_data.get("password", "N/A")  # Şifreyi düz metin olarak saklıyorsanız burada görünür
            print(f"ID: {user_id}, Username: {username}, Role: {role}, Password: {password}")
       


    def show_student_screen(self):
        """
        Terminal tabanlı öğrenci menüsü.
        """
        while True:
            print(f"\nWelcome {self.username} {self.surname}!")
            print(f"School: {self.school_name} | Class: {self.class_number}")  # Yeni alanları göster
            print("1. View Exam Results")
            print("2. Start Exam")
            print("3. Exit")

            try:
                choice = int(input("\nEnter your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 3.")
                continue

            if choice == 1:
                self.show_exam_results()
            elif choice == 2:
                self.start_exam()
            elif choice == 3:
                print("Exiting the student menu. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 3.")

    def show_exam_results(self):
        """
        Sınav sonuçlarını terminalde göster.
        """
        print("\n=== Student Information ===")
        print(f"Name: {self.username} {self.surname}")
        print(f"School: {self.school_name}")
        print(f"Class: {self.class_number}")
        print("\n=== Exam Results ===")
        results = "\n".join(
            f"{section}: {score}/100"
            for section, score in self.success_per_section.items()
        )
        overall_score = self.get_score()
        print(f"{results}\nOverall Score: {overall_score:.2f}%")

    def has_attempts_left(self):
        return self.attempts < self.max_attempts

    def increment_attempts(self):
        self.attempts += 1

    def update_score(self, section, correct_answers, total_questions):
        section_score = round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0
        self.success_per_section[section] = section_score
        self.calculate_overall_score()

    def calculate_overall_score(self):
        total_score = sum(self.success_per_section.values())
        self.score = round(total_score / len(self.success_per_section), 2)

    def get_score(self):
        return round(self.score, 2)
    

    def show_teacher_screen(self):
     
        # Terminal tabanlı öğretmen menüsü.
     
        while True:
            print(f"\nWelcome {self.username} {self.surname}!")
            print(f"role: {self.subject}")
            print("1. View Exam Results (Filtered by your subject)")
            print("2. View School Results (Select a school)")
            print("3. View Class Results (Select a class)")
            print("4. Exit")

            try:
                choice = int(input("\nEnter your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 4.")
                continue

            if choice == 1:
                self.view_exam_results()
            elif choice == 2:
                self.view_school_results()
            elif choice == 3:
                self.view_class_results()
            elif choice == 4:
                print("Exiting the teacher menu. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")

    def view_exam_results(self):
    
    # Öğretmenin branşı ile ilgili sınav sonuçlarını görüntüler.
    
        try:
            with open("user/users.json", "r") as f:
                users_data = json.load(f)

            print("\n--- Exam Results for Your Subject ---")
            for user_data in users_data.values():
                # Sadece öğrencilere ait veriler ve öğretmenin branşı ile ilgili sonuçlar
                if user_data.get("student_number") and self.role in user_data["success_per_section"]:
                    student_name = user_data["username"]
                    subject_score = user_data["success_per_section"].get(self.role, "N/A")
                    print(f"Student: {student_name}, Score in {self.role}: {subject_score}/100")
        except FileNotFoundError:
            print("User data file not found.")
        except json.JSONDecodeError:
            print("User data file is empty or corrupted.")

            


    def view_school_results(self):
        """
        Seçilen okulun ortalamasını ve genel ortalamayı görüntüler.
        """
        try:
            with open("user/users.json", "r") as f:
                users_data = json.load(f)    

            schools = set(
                user_data.get("school_name", "Unknown") 
                for user_data in users_data.values() 
                if "school_name" in user_data
              )

            if not schools:
                print("No schools found in the data.")
                return

            print("\nAvailable Schools:")
            for i, school in enumerate(schools, 1):
                print(f"{i}. {school}")

            try:
                school_choice = int(input("Select a school by number: ").strip())
                if not (1 <= school_choice <= len(schools)):
                    print("Invalid choice. Returning to menu.")
                    return
            except ValueError:
                print("Invalid input. Returning to menu.")
                return

            selected_school = list(schools)[school_choice - 1]

            school_scores = []
            overall_scores = []
            for user_data in users_data.values():
                if user_data.get("student_number"):
                    overall_scores.extend(user_data["success_per_section"].values())
                    if user_data.get("school_name") == selected_school:
                        school_scores.extend(user_data["success_per_section"].values())

            school_average = round(sum(school_scores) / len(school_scores), 2) if school_scores else 0
            overall_average = round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else 0

            print(f"\n--- Results for {selected_school} ---")
            print(f"School Average: {school_average}%")
            print(f"Overall Average (All Schools): {overall_average}%")
        except FileNotFoundError:
            print("User data file not found.")
        except json.JSONDecodeError:
            print("User data file is empty or corrupted.")

    def list_users(self, role=None):
        """List users based on optional role filter."""
        try:
            with open("user/users.json", "r") as f:
                users_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("No users found.")
            return []

        filtered_users = []
        for unique_id, user_data in users_data.items():
            if role is None or user_data.get('role') == role:
                user_info = {
                    'id': unique_id,
                    'username': user_data.get('username', 'N/A'),
                    'role': user_data.get('role', 'N/A')
                }
                filtered_users.append(user_info)
        return filtered_users

    def update_user(self, user_id):
        """Update user details"""
        try:
            with open("user/users.json", "r") as f:
                users_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("No users found.")
            return

        if user_id not in users_data:
            print("User not found.")
            return

        user_data = users_data[user_id]
        
        print("\nCurrent User Details:")
        for key, value in user_data.items():
            print(f"{key}: {value}")

        print("\nWhich field do you want to update?")
        fields = list(user_data.keys())
        for i, field in enumerate(fields, 1):
            print(f"{i}. {field}")

        try:
            choice = int(input("Enter the number of the field to update: "))
            field = fields[choice - 1]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

        new_value = input(f"Enter new value for {field}: ")
        user_data[field] = new_value

        users_data[user_id] = user_data
        with open("user/users.json", "w") as f:
            json.dump(users_data, f, indent=4)

        print(f"User {user_id} updated successfully.")        

    def view_class_results(self):
        
          #Seçilen sınıfın ortalaması ve doğru-yanlış cevap analizlerini görüntüler.
          
        try:
            with open("user/users.json", "r") as f:
                users_data = json.load(f)

            classes = set(
                user_data.get("class_number", "Unknown") 
                for user_data in users_data.values() 
                if "class_number" in user_data
               )

            if not classes:
                print("No classes found in the data.")
                return

            print("\nAvailable Classes:")
            for i, class_name in enumerate(classes, 1):
               print(f"{i}. {class_name}")

            try:
                class_choice = int(input("Select a class by number: ").strip())
                if not (1 <= class_choice <= len(classes)):
                    print("Invalid choice. Returning to menu.")
                    return
            except ValueError:
                print("Invalid input. Returning to menu.")
                return

            selected_class = list(classes)[class_choice - 1]

            class_scores = []
            correct_analysis = {}
            incorrect_analysis = {}

            for user_data in users_data.values():
                if user_data.get("student_number") and user_data.get("class_number") == selected_class:
                    for section, score in user_data["success_per_section"].items():
                        if section not in correct_analysis:
                            correct_analysis[section] = 0
                            incorrect_analysis[section] = 0
                        correct_analysis[section] += score
                        incorrect_analysis[section] += (100 - score)  # Yanlışlar için kalan yüzdelik

                    class_scores.extend(user_data["success_per_section"].values())

            class_average = round(sum(class_scores) / len(class_scores), 2) if class_scores else 0

            print(f"\n--- Results for Class {selected_class} ---")
            print(f"Class Average: {class_average}%")

            print("\n--- Correct Answer Analysis ---")
            for section, correct in correct_analysis.items():
                print(f"{section}: {round(correct, 2)}%")

            print("\n--- Incorrect Answer Analysis ---")
            for section, incorrect in incorrect_analysis.items():
                print(f"{section}: {round(incorrect, 2)}%")
        except FileNotFoundError:
            print("User data file not found.")
        except json.JSONDecodeError:
            print("User data file is empty or corrupted.")



        
        