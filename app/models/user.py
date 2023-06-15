import bcrypt
from datetime import date, datetime
from pydantic import BaseModel, Field, EmailStr, AnyUrl, SecretStr
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from typing import Literal, List, Optional
from uuid import uuid4

from ..db import orm

class Address(BaseModel):
    address: str
    city : str
    postalCode: int
    state: str
    primary: bool
    label : Literal['home','work']

class UserRegistration(BaseModel):
    email : EmailStr
    userName : str
    password : SecretStr
    googleId : str | None = None
    facebookId : str | None = None

    def update_user_with_social(cls, db:Session):
        stmt = 'update users set googleId = :x, facebookId = :y where email= :z'
        db.execute(text(stmt) ,
                   dict(x=cls.googleId,y=cls.facebookId,z=cls.email))
        db.commit()
        return db.query(orm.User).filter(orm.User.email == cls.email).first()

class User(UserRegistration):
    id : str = Field(str(uuid4()),description="Auto generated User Id on registration")
    keycloakId : str
    permissionLevel : Literal["Customer","Admin","Supplier"] = "Customer"
    emailVerified : bool = False
    firstName : str = ""
    lastName : str = ""
    gender :  Literal["male","female"] = "male"
    phone : str = ""
    birthDate : date = datetime.now().date()
    avatar : Optional[AnyUrl] 
    addresses : List[Address] = []
    status : Literal["active","closed"] = "active"
    modifiedAt : datetime = datetime.now()
    createdAt : datetime = datetime.now()

    class Config():
        orm_mode = True

    @classmethod
    def hash_password(cls, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(14))

    @classmethod
    def verify_password(cls, hashed, password):
        return bcrypt.checkpw(password, hashed)

    def register_user(cls, db: Session):
        cls.password = cls.hash_password(cls.password)
        db_user = orm.User(**cls.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @classmethod
    def get_user(cls,db: Session, id:str = None, email:str= None, userName:str = None,
                  facebookId: str = None, googleId: str = None):
        if id:
            cond = (orm.User.id == id)
        elif facebookId:
            cond = (orm.User.facebookId == facebookId)
        elif googleId:
            cond = (orm.User.googleId == googleId)
        elif email or userName:
            cond = or_(orm.User.email == email,
                     orm.User.userName == userName)
        user = db.query(orm.User).filter(cond).first()
        return user

    @classmethod
    def get_users(cls, db:Session, offset: int, limit: int):
        return db.query(orm.User).offset(offset).limit(limit).all()
