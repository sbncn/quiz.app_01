import json
import psycopg2
import time
import os
import random
from psycopg2.extras import execute_batch  # Performans için
import tools.main_defs as md
from dotenv import load_dotenv

# .env dosyasını yükle
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

# Veritabanındaki tüm tabloları sil
def clear_database(cursor):
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        print(f"Tablo {table_name} silindi.")

def normalize_section_name(section_name):
    """
    Section name'i normalize eder.
    Örnek: 'questions_section1.json' -> 'English'
    """
    section_map = {
        "questions_section1.json": "English",
        "answers_section1": "English",
        "questions_section2.json": "Computer",
        "answers_section2": "Computer",
        "questions_section3.json": "History",
        "answers_section3": "History",
        "questions_section4.json": "Geography",
        "answers_section4": "Geography"
    }
    return section_map.get(section_name, section_name)  # Eğer eşleşme yoksa orijinal section_name'i döndür


# Users tablosunu oluşturma
def create_users_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT,
        name TEXT,
        surname TEXT,
        school_name TEXT,
        class_number TEXT,
        subject TEXT,
        is_admin BOOLEAN DEFAULT FALSE,
        attempts INT DEFAULT 0,
        max_attempts INT DEFAULT 2,
        student_number VARCHAR(10) UNIQUE,
        teacher_id VARCHAR(10) UNIQUE
    );
    """
    cursor.execute(create_table_query)
    print("Users tablosu başarıyla oluşturuldu.")

def create_results_table(cursor):
    """
    Veritabanında results tablosunu oluşturur.
    """
    # Creating the results table
    create_results_query = """
    CREATE TABLE IF NOT EXISTS results (
        id SERIAL PRIMARY KEY,
        student_number TEXT NOT NULL,
        exam_attempt INT NOT NULL,
        subject TEXT NOT NULL,
        score FLOAT,
        true_count INT,
        false_count INT
    );
    """
    
    try:
        cursor.execute(create_results_query)
        print("Results tablosu başarıyla oluşturuldu.")
        
        # Creating indexes to speed up queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_student_number ON results(student_number);
        """)
        print("Index başarıyla oluşturuldu (student_number).")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_exam_attempt ON results(exam_attempt);
        """)
        print("Index başarıyla oluşturuldu (exam_attempt).")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subject ON results(subject);
        """)
        print("Index başarıyla oluşturuldu (subject).")
    
    except Exception as e:
        print(f"Tablolar oluşturulurken bir hata oluştu: {e}")


def create_answers_table(cursor):
    """
    Veritabanında answers tablosunu oluşturur.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS answers (
        id SERIAL PRIMARY KEY,
        section_name TEXT NOT NULL,
        question_id INT NOT NULL,
        answer TEXT NOT NULL
    );
    """
    cursor.execute(create_table_query)
    print("Answers tablosu başarıyla oluşturuldu.")

def create_questions_table(cursor):
    """
    Veritabanında questions tablosunu oluşturur.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        section_name TEXT NOT NULL,
        question_id INT NOT NULL,
        question_text TEXT NOT NULL,
        question_type TEXT NOT NULL,
        options TEXT[],  -- This is where the options are stored as an array of text
        score INT NOT NULL
    );
    """
    cursor.execute(create_table_query)
    print("Questions tablosu başarıyla oluşturuldu.")
def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"{file_path} dosyası okunamadı: {e}")
        return {}

# Users tablosuna veri ekleme
def insert_users_data(cursor, users_data):
    query = """
        INSERT INTO users (username, password, role, name, surname, student_number, teacher_id, school_name, class_number, subject, is_admin, attempts, max_attempts)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        user_records = []
        for user_id, user in users_data.items():
            user_records.append((
                user["username"],
                user["password"],
                user["role"],
                user.get("name"),
                user.get("surname"),
                user.get("student_number"),
                user.get("teacher_id"),
                user.get("school_name"),
                user.get("class_number"),
                user.get("subject"),
                user.get("is_admin", False),  # Burada is_admin kullanılıyor
                user.get("attempts", 0),
                user.get("max_attempts", 2)
            ))
        execute_batch(cursor, query, user_records)
        print(f"{len(user_records)} kullanıcı eklendi.")
    except Exception as e:
        print(f"Users tablosuna veri eklenirken hata oluştu: {e}")

# Results tablosuna veri ekleme

def insert_results_data(cursor, users_data):
    """
    Users JSON dosyasındaki exam_results verilerini results tablosuna ekler.
    """
    insert_result_query = """
    INSERT INTO results (student_number, exam_attempt, subject, score, true_count, false_count)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;  -- Get the ID of the inserted result
    """
    
    try:
        for user_id, user in users_data.items():
            student_number = user.get("student_number")
            exam_results = user.get("exam_results", [])
            
            # Her sınav denemesi için veri ekle
            for attempt_index, exam_result in enumerate(exam_results):
                for subject, details in exam_result.items():
                    if subject != "overall_score":  # overall_score hariç diğer dersler
                        score = details.get("score", 0.0)
                        true_count = details.get("true_count", 0)
                        false_count = details.get("false_count", 0)
                        
                        # Insert exam result into results table
                        cursor.execute(insert_result_query, (
                            student_number,
                            attempt_index + 1,  # Attempt numarası 1'den başlar
                            subject.replace("_score", ""),  # Konu adını düzenle
                            score,
                            true_count,
                            false_count
                        ))
                        
                        # Get the ID of the inserted result
                        result_id = cursor.fetchone()[0]  # The result_id will not be used further since we removed the exam_questions part

        print(f"Veriler başarıyla eklendi.")
    except Exception as e:
        print(f"Veri eklerken hata oluştu: {e}")


def insert_answer_to_db(cursor, section_name, records):
    """
    Verilen section_name ve records ile answers tablosuna veri ekler.
    """
    normalized_section_name = normalize_section_name(section_name)
    insert_query = """
        INSERT INTO answers (section_name, question_id, answer)
        VALUES (%s, %s, %s)
    """
    values = []
    for record in records:
        question_id = record['id']
        answers = record['answer']

        if isinstance(answers, list):
            for answer in answers:
                values.append((normalized_section_name, question_id, answer))
        else:
            values.append((normalized_section_name, question_id, answers))

    execute_batch(cursor, insert_query, values)
    print(f"Answers for section '{section_name}' başarıyla eklendi.")

def insert_question_to_db(cursor, section_name, records):
    """
    Verilen section_name ve records ile questions tablosuna veri ekler.
    """
    normalized_section_name = normalize_section_name(section_name)
    insert_query = """
        INSERT INTO questions (section_name, question_id, question_text, question_type, options, score)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = []
    for record in records:
        question_id = record.get('id')
        question_text = record.get('question_text')
        question_type = record.get('type')
        options = record.get('options', [])
        score = record.get('score')

        if not question_id or not question_text or not question_type or score is None:
            print(f"Skipping invalid question record: {record}")
            continue

        values.append((normalized_section_name, question_id, question_text, question_type, options, score))

    execute_batch(cursor, insert_query, values)
    print(f"Questions for section '{section_name}' başarıyla eklendi.")


# Ana işlem
def setup():
    BASE_DIR = "/app"  # Docker konteynerindeki ana dizin
    
    # Dosya yollarını güncelledik
    users_json_file_path = os.path.join(BASE_DIR, 'user', 'users.json')
    answers_json_file_path = os.path.join(BASE_DIR, 'answers', 'answers.json')

    # Questions JSON dosyalarını dizininde okuma
    questions_json_files = [
        'questions_section1.json',
        'questions_section2.json',
        'questions_section3.json',
        'questions_section4.json'
    ]

    try:
        print("Veritabanına bağlanılıyor...")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Veritabanındaki tüm tabloları sil
                clear_database(cursor)

                # Tablo oluşturma
                create_users_table(cursor)
                create_results_table(cursor)
                create_answers_table(cursor)
                create_questions_table(cursor)

                # Users JSON dosyasını yükle
                print(f"JSON dosyası {users_json_file_path} yükleniyor...")
                users_data = read_json(users_json_file_path)
                if users_data:
                    insert_users_data(cursor, users_data)
                    insert_results_data(cursor, users_data)

                # Answers JSON dosyasını yükle
                print(f"JSON dosyası {answers_json_file_path} yükleniyor...")
                answers_data = read_json(answers_json_file_path)
                if answers_data:
                    for section_name, records in answers_data.items():
                        if isinstance(records, list):
                            insert_answer_to_db(cursor, section_name, records)

                # Questions JSON dosyalarını yükle
                for json_file in questions_json_files:
                    json_file_path = os.path.join(BASE_DIR, 'questions', json_file)
                    print(f"JSON dosyası {json_file_path} yükleniyor...")
                    questions_data = read_json(json_file_path)
                    if isinstance(questions_data, list):
                        insert_question_to_db(cursor, json_file, questions_data)

                conn.commit()
                print("Veriler başarıyla eklendi.")
    except psycopg2.Error as e:
        print(f"Veritabanı hatası: {e}")
    except (IOError, json.JSONDecodeError) as e:
        print(f"Dosya okuma veya JSON hatası: {e}")
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
    else:
        print("İşlem tamamlandı.")
        