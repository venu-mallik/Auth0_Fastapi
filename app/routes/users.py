from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..models.user import User, UserRegistration
from .utils import get_db, TPC, decode_token

router = APIRouter(prefix="/users")


@router.get("/users", dependencies=[Depends(TPC(["Admin"]))] ,response_model=list[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = User.get_users(db, skip, limit)
    return users

@router.get("/users/{user_id}", response_model= User)
def read_user(user_id: str, db: Session = Depends(get_db), token = Depends(TPC(["Admin","Customer"]))):
    if "Admin" not in token.get('scope',[]):
        user_id = token['sub']
    db_user = User.get_user(db, id= user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

