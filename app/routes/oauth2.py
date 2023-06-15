from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated

from ..models.user import User, UserRegistration
from .utils import get_db, auth0, encode_token, decode_token

router = APIRouter(prefix="/oauth2")

@router.post("/token")
async def login_user( form_data: Annotated[OAuth2PasswordRequestForm, Depends()] , 
                     facebookId : str = None, googleId : str = None, db: Session = Depends(get_db)):
    if facebookId :
        db_user = User.get_user(facebookId=facebookId)
    elif googleId:
        db_user = User.get_user(googleId=googleId)
    else:
        db_user = User.get_user(db, userName= form_data.username, email=form_data.username)
    if db_user and User.verify_password( db_user.password, form_data.password):
        body= { "sub": db_user.id, "uid": db_user.keycloakId , "typ": "accessToken"}
        idBody = { **body, "name": db_user.userName, "firstName" : db_user.firstName,
                  "lastName" : db_user.lastName,   "typ": "idToken" }
        return {"id" : db_user.id, "idToken" :  encode_token(idBody), "accessToken": encode_token(body)}
    else :
        raise HTTPException(status_code=403, detail="Incorrect credentials")
        

@router.post("/register", response_model=User)
async def create_user(user: UserRegistration, db: Session = Depends(get_db)):
    try:
        db_user = User.get_user(db, email=user.email, userName= user.userName)
        if db_user:
            if db_user.googleId and db_user.facebookId:
                raise HTTPException(status_code=400, detail="Email already registered or Linked")
            elif  db_user.facebookId is None and user.facebookId:
                rec = auth0.users.get(user.facebookId)
                [conn, _ ] = resp['user_id'].split("|")
                auth0.users.link_user_account(db_user.keycloakId,{'provider': conn, 'user_id' : rec['user_id']})
            else:
                # If New connection added for same email which is not linked, link it automatically 
                users = auth0.users_by_email.search_users_by_email(user.email)
                for rec in users:
                    if db_user.keycloakId == rec['user_id']:
                        continue
                    [conn, _ ] = rec['user_id'].split("|")
                    auth0.users.link_user_account(db_user.keycloakId,{'provider': conn, 'user_id' : rec['user_id']})
                    if 'google-oauth2' in rec['user_id']:
                        user.googleId = rec['user_id']
            ans = user.update_user_with_social(db=db)
            return ans
            
        resp = auth0.users.create( {'email': user.email , 'password': user.password ,
                                 'connection' :  'Username-Password-Authentication' })
        user = User(**resp,password= user.password, userName= resp['nickname'], keycloakId=resp['user_id'], 
                avatar=resp['picture'], googleId=None, facebookId=None)
        return user.register_user(db=db)
    except Exception:
        raise HTTPException(status_code=400, detail="Email already registered or Linked")

@router.post("/refresh_token")
async def refresh_token( token: str = Depends(decode_token)):
    if token['sub']:
        return {"id" : token['sub'], "token": encode_token(token)}
    else :
        raise HTTPException(status_code=403, detail="Invalid Token")
        
