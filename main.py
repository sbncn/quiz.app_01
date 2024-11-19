import json
import random
import time
import hashlib
import os
from datetime import datetime

class ExamApp:
    def __init__(self):
        self.current_user = None
        self.exam_duration = 600  # 10 dakika (saniye cinsinden)
        self.required_score = 75  # Geçme notu yüzdesi
        
    def hash_password(self, password):
        """Şifreyi güvenli bir şekilde hashler."""
        try:
            return hashlib.sha256(password.encode()).hexdigest()
        except Exception as e:
            print(f"Şifre hashleme hatası: {e}")
            return None

    def load_users(self):
        """Kullanıcı bilgilerini yükler."""
        try:
            if not os.path.exists('user/user.json'):
                os.makedirs('user', exist_ok=True)
                return {}
            with open('user/user.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Kullanıcı bilgileri yükleme hatası: {e}")
            return {}

    def save_users(self, users):
        """Kullanıcı bilgilerini kaydeder."""
        try:
            os.makedirs('user', exist_ok=True)
            with open('user/user.json', 'w') as f:
                json.dump(users, f, indent=4)
        except Exception as e:
            print(f"Kullanıcı bilgileri kaydetme hatası: {e}")

    def register(self, name, surname, password):
        """Yeni kullanıcı kaydı oluşturur."""
        try:
            users = self.load_users()
            user_id = f"{name.lower()}_{surname.lower()}"
            
            if user_id in users:
                print("Bu kullanıcı zaten kayıtlı!")
                return False
            
            users[user_id] = {
                'name': name,
                'surname': surname,
                'password': self.hash_password(password),
                'exam_count': 0
            }
            
            self.save_users(users)
            print("Kayıt başarılı!")
            return True
        except Exception as e:
            print(f"Kayıt hatası: {e}")
            return False

    def login(self, name, surname, password):
        """Kullanıcı girişi yapar."""
        try:
            users = self.load_users()
            user_id = f"{name.lower()}_{surname.lower()}"
            
            if user_id not in users:
                print("Kullanıcı bulunamadı!")
                return False
            
            if users[user_id]['password'] != self.hash_password(password):
                print("Yanlış şifre!")
                return False
            
            if users[user_id]['exam_count'] >= 2:
                print("Maksimum sınav hakkınızı kullandınız!")
                return False
            
            self.current_user = user_id
            print("Giriş başarılı!")
            return True
        except Exception as e:
            print(f"Giriş hatası: {e}")
            return False

    def load_questions(self):
        """Sınav sorularını yükler."""
        try:
            questions = {}
            for section in range(1, 5):
                with open(f'questions/section{section}.json', 'r', encoding='utf-8') as f:
                    questions[f'section{section}'] = json.load(f)
            return questions
        except Exception as e:
            print(f"Soru yükleme hatası: {e}")
            return None

    def select_random_questions(self):
        """Her sectiondan rastgele sorular seçer."""
        try:
            questions = self.load_questions()
            selected_questions = []
            
            # Her sectiondan rastgele sorular seç
            for section in range(1, 5):
                section_questions = questions[f'section{section}']
                selected = random.sample(section_questions, 2 if section == 3 else 3)
                for q in selected:
                    q['section'] = section
                selected_questions.extend(selected)
            
            random.shuffle(selected_questions)
            return selected_questions
        except Exception as e:
            print(f"Soru seçme hatası: {e}")
            return None

    def calculate_section_score(self, answers, section):
        """Section bazında puanları hesaplar."""
        try:
            total_points = 0
            max_points = 0
            
            for q in answers:
                if q['section'] == section:
                    if section == 1:  # Doğru/Yanlış
                        max_points += 5
                        if q['user_answer'] == q['correct_answer']:
                            total_points += 5
                    elif section == 2:  # Çoktan seçmeli
                        max_points += 5
                        if q['user_answer'] == q['correct_answer']:
                            total_points += 5
                    elif section == 3:  # İki doğru cevaplı
                        max_points += 10
                        if set(q['user_answer']) == set(q['correct_answer']):
                            total_points += 10
                    elif section == 4:  # Sıralama
                        max_points += 20
                        if q['user_answer'] == q['correct_answer']:
                            total_points += 20
            
            percentage = (total_points / max_points * 100) if max_points > 0 else 0
            return percentage
        except Exception as e:
            print(f"Puan hesaplama hatası: {e}")
            return 0

    def save_result(self, answers, total_score):
        """Sınav sonuçlarını kaydeder."""
        try:
            os.makedirs('results', exist_ok=True)
            
            users = self.load_users()
            users[self.current_user]['exam_count'] += 1
            self.save_users(users)
            
            result = {
                'user_id': self.current_user,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_score': total_score,
                'answers': answers,
                'passed': total_score >= self.required_score
            }
            
            results_file = 'results/exam_results.json'
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
            except FileNotFoundError:
                results = []
            
            results.append(result)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=4)
                
        except Exception as e:
            print(f"Sonuç kaydetme hatası: {e}")

    def conduct_exam(self):
        """Sınavı yönetir."""
        try:
            if not self.current_user:
                print("Önce giriş yapmalısınız!")
                return
            
            questions = self.select_random_questions()
            if not questions:
                return
            
            start_time = time.time()
            answers = []
            current_question = 0
            
            while current_question < len(questions):
                elapsed_time = time.time() - start_time
                remaining_time = self.exam_duration - elapsed_time
                
                if remaining_time <= 0:
                    print("\nSüre doldu!")
                    break
                
                if remaining_time <= 60:
                    print("\nDİKKAT: Son 1 dakika!")
                
                question = questions[current_question]
                print(f"\nSoru {current_question + 1}/{len(questions)}")
                print(f"Kalan süre: {int(remaining_time)} saniye")
                print(question['question'])
                
                if question['section'] == 1:  # Doğru/Yanlış
                    print("1: Doğru, 0: Yanlış")
                    answer = input("Cevabınız: ").strip()
                    question['user_answer'] = int(answer)
                
                elif question['section'] == 2:  # Çoktan seçmeli
                    for i, option in enumerate(question['options']):
                        print(f"{i+1}: {option}")
                    answer = input("Cevabınız: ").strip()
                    question['user_answer'] = int(answer)
                
                elif question['section'] == 3:  # İki doğru cevap
                    for i, option in enumerate(question['options']):
                        print(f"{i+1}: {option}")
                    answer = input("İki cevabınızı virgülle ayırarak girin: ").strip()
                    question['user_answer'] = [int(x) for x in answer.split(',')]
                
                elif question['section'] == 4:  # Sıralama
                    for i, option in enumerate(question['options']):
                        print(f"{i+1}: {option}")
                    answer = input("Sıralamayı virgülle ayırarak girin: ").strip()
                    question['user_answer'] = [int(x) for x in answer.split(',')]
                
                answers.append(question)
                
                if current_question < len(questions) - 1:
                    nav = input("\nSonraki soru için 'n', önceki soru için 'p': ").strip().lower()
                    if nav == 'p' and current_question > 0:
                        current_question -= 1
                    else:
                        current_question += 1
                else:
                    current_question += 1
            
            # Puanları hesapla
            section_scores = []
            for section in range(1, 5):
                score = self.calculate_section_score(answers, section)
                section_scores.append(score)
                print(f"Section {section} puanı: {score:.2f}%")
            
            total_score = sum(section_scores) / len(section_scores)
            print(f"\nToplam puan: {total_score:.2f}%")
            print("Başarılı!" if total_score >= self.required_score else "Başarısız!")
            
            self.save_result(answers, total_score)
            
        except Exception as e:
            print(f"Sınav yürütme hatası: {e}")

    def view_results(self, is_admin=False):
        """Sınav sonuçlarını görüntüler."""
        try:
            if not os.path.exists('results/exam_results.json'):
                print("Henüz sonuç bulunmamaktadır.")
                return
            
            with open('results/exam_results.json', 'r') as f:
                results = json.load(f)
            
            if not is_admin:
                results = [r for r in results if r['user_id'] == self.current_user]
            
            for result in results:
                print("\n--- Sınav Sonucu ---")
                print(f"Kullanıcı: {result['user_id']}")
                print(f"Tarih: {result['date']}")
                print(f"Toplam Puan: {result['total_score']:.2f}%")
                print(f"Sonuç: {'Başarılı' if result['passed'] else 'Başarısız'}")
                
        except Exception as e:
            print(f"Sonuç görüntüleme hatası: {e}")

def main():
    try:
        app = ExamApp()
        
        while True:
            print("\n--- Sınav Uygulaması ---")
            print("1. Giriş")
            print("2. Kayıt")
            print("3. Sınava Başla")
            print("4. Sonuçları Görüntüle")
            print("5. Admin Girişi")
            print("6. Çıkış")
            
            choice = input("Seçiminiz: ").strip()
            
            if choice == '1':
                name = input("Ad: ")
                surname = input("Soyad: ")
                password = input("Şifre: ")
                app.login(name, surname, password)
                
            elif choice == '2':
                name = input("Ad: ")
                surname = input("Soyad: ")
                password = input("Şifre: ")
                app.register(name, surname, password)
                
            elif choice == '3':
                app.conduct_exam()
                
            elif choice == '4':
                app.view_results()
                
            elif choice == '5':
                admin_password = input("Admin şifresi: ")
                if admin_password == "admin123":  # Gerçek uygulamada daha güvenli bir yöntem kullanılmalı
                    app.view_results(is_admin=True)
                else:
                    print("Yanlış admin şifresi!")
                    
            elif choice == '6':
                print("Çıkış yapılıyor...")
                break
                
            else:
                print("Geçersiz seçim!")
                
    except Exception as e:
        print(f"Ana program hatası: {e}")

if __name__ == "__main__":
    main()