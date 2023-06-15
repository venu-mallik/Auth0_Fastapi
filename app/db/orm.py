from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date
from sqlalchemy.orm import relationship

from .setup import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    keycloakId = Column(String)
    email = Column(String, unique=True, index=True)
    emailVerified = Column(Boolean)
    googleId = Column(String,nullable=True)
    facebookId = Column(String,nullable=True)
    userName = Column(String, unique=True, index=True)
    password = Column(String)
    permissionLevel = Column(String)
    firstName = Column(String)
    lastName = Column(String) 
    gender = Column(String)
    phone = Column(String)
    birthDate = Column(Date)
    avatar = Column(String)
    status = Column(String)
    modifiedAt = Column(DateTime)
    createdAt =  Column(DateTime)
    addresses = relationship("Address")
    

class Address(Base):
    __tablename__ = "address"

    id = Column(String, primary_key=True, index=True)
    address = Column(String)
    city = Column(String)
    postalCode = Column(Integer)
    state = Column(String)
    label = Column(String)
    primary = Column(Boolean)
    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="addresses")

