# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from uuid import UUID  # UUID türünü ekleyin
from typing import Optional, List
from tools.database import get_db
from tools.models import User
from tools.user import add_user, delete_user, update_user
from tools.token_generator import get_current_user
from tools.utils import hash_password

router = APIRouter()

# ========== Pydantic Models ==========

class UserResponse(BaseModel):
    user_id: UUID  # str yerine UUID kullanın
    username: str
    role: str
    class_name: str
    school_id: UUID  # str yerine UUID kullanın
    name: str
    surname: str

    class Config:
        orm_mode = True  # SQLAlchemy model -> Pydantic

class UpdateUserRequest(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    class_name: Optional[str]
    role: Optional[str]
    registered_section: Optional[str]
    new_password: Optional[str]  # <-- Eklendi: admin isteyince parolayı da değiştirebilir.

# ========== Endpoints ==========

@router.get("/", response_model=List[UserResponse], summary="List all users")
def list_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can list users.")
    # Sorgu
    users = db.query(User).all()
    # FastAPI otomatik olarak her User nesnesini UserResponse’a dönüştürecek (orm_mode = True).
    return users

@router.delete("/{username}", summary="Delete a user")
def delete_user_endpoint(username: str,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users.")
    success = delete_user(db, current_user, username)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or not deleted.")
    return {"message": f"User {username} deleted successfully."}

@router.put("/{username}", summary="Update a user")
def update_user_endpoint(username: str,
                         request: UpdateUserRequest,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users.")

    update_fields = {}
    if request.name is not None:
        update_fields["name"] = request.name
    if request.surname is not None:
        update_fields["surname"] = request.surname
    if request.class_name is not None:
        update_fields["class_name"] = request.class_name
    if request.role is not None:
        update_fields["role"] = request.role
    if request.registered_section is not None:
        update_fields["registered_section"] = request.registered_section

    # Eğer new_password geldiyse hash'leyip 'password' alanına atayacağız.
    if request.new_password is not None and request.new_password.strip() != "":
        hashed = hash_password(request.new_password.strip())
        update_fields["password"] = hashed

    success = update_user(db, current_user, username, **update_fields)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or not updated.")
    return {"message": f"User {username} updated successfully."}
