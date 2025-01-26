# tools/user.py

from sqlalchemy.orm import Session
from tools.utils import hash_password, check_password
from tools.models import User, School
import os

# Eğer teachers "matematik","ingilizce","fizik","kimya" seçerse bunları int'e mapleyelim:
SECTION_MAPPING = {
    "matematik": "1",
    "ingilizce": "2",
    "fizik": "3",
    "kimya": "4"
}
# Boşsa "" veya None kalsın (student vs.)

def register_user(db: Session, username, password, name, surname, class_name, role, registered_section=None):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print("Username already exists.")
        return False

    default_school = db.query(School).filter(School.name == "DefaultSchool").first()
    if not default_school:
        print("DefaultSchool not found.")
        return False

    # Eğer role teacher ise ve registered_section "matematik" vs. geldiyse "1" "2" ... saklayalım
    if role.lower() == "teacher" and registered_section:
        if registered_section in SECTION_MAPPING:
            registered_section = SECTION_MAPPING[registered_section]

    hashed_pw = hash_password(password)
    user = User(
        username=username,
        password=hashed_pw,
        name=name,
        surname=surname,
        role=role.lower(),
        class_name=class_name,
        registered_section=registered_section or "",
        school_id=default_school.school_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print("Registration successful.")
    return True

def login_user(db: Session, username, password):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print("User not found.")
        return None
    if check_password(password, user.password):
        print(f"Welcome, {user.name} {user.surname}!")
        return user
    else:
        print("Incorrect password.")
        return None

def add_user(db: Session, admin_user, **kwargs):
    if admin_user.role.lower() != 'admin':
        print("Only admins can add users.")
        return False
    return register_user(db, **kwargs)

def delete_user(db: Session, admin_user, username):
    if admin_user.role.lower() != 'admin':
        print("Only admins can delete users.")
        return False
    user = db.query(User).filter(User.username == username).first()
    if user:
        db.delete(user)
        db.commit()
        print("User deleted.")
        return True
    else:
        print("User not found.")
        return False

def update_user(db: Session, admin_user, username, **kwargs):
    if admin_user.role.lower() != 'admin':
        print("Only admins can update users.")
        return False

    user = db.query(User).filter(User.username == username).first()
    if not user:
        print("User not found.")
        return False

    # Burada da teacher's "matematik" -> "1" mapping
    if "role" in kwargs and kwargs["role"] and kwargs["role"].lower() == "teacher":
        # eğer teacher ise ve 'registered_section' parametresi geldiyse mapping'e bak
        if "registered_section" in kwargs and kwargs["registered_section"]:
            rs = kwargs["registered_section"]
            if rs in SECTION_MAPPING:
                kwargs["registered_section"] = SECTION_MAPPING[rs]

    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            # Parola güncelleniyorsa hash'leyelim
            if key == "password":
                value = hash_password(value)
            setattr(user, key, value)

    db.commit()
    print("User updated.")
    return True

def create_admin_user(engine):
    from sqlalchemy.orm import sessionmaker
    from tools.models import User, School
    from dotenv import load_dotenv
    load_dotenv()
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_NAME = os.getenv("ADMIN_NAME")
    ADMIN_SURNAME = os.getenv("ADMIN_SURNAME")
    # Create a new session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if admin:
            print("Admin user already exists.")
            return
        # Get default school
        default_school = db.query(School).filter(School.name == "DefaultSchool").first()
        if not default_school:
            print("DefaultSchool not found. Creating DefaultSchool.")
            default_school = School(name="DefaultSchool")
            db.add(default_school)
            db.commit()
            db.refresh(default_school)
        # Create admin user
        hashed_pw = hash_password(ADMIN_PASSWORD)
        admin_user = User(
            username=ADMIN_USERNAME,
            password=hashed_pw,
            name=ADMIN_NAME,
            surname=ADMIN_SURNAME,
            role="admin",
            class_name="",
            school_id=default_school.school_id,
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()