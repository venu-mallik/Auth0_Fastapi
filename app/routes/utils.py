from auth0.authentication import  GetToken
from auth0.management import Auth0
from fastapi import Request, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseSettings

from datetime import datetime, timedelta
import jwt

class Settings(BaseSettings):
    auth0_domain_id : str
    auth0_client_id : str
    auth0_client_secret : str
    jwt_secret: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

k = Settings()

get_token = GetToken( k.auth0_domain_id , k.auth0_client_id, client_secret= k.auth0_client_secret)
token = get_token.client_credentials('https://{}/api/v2/'.format(k.auth0_domain_id))
mgmt_api_token = token['access_token']
auth0 = Auth0(k.auth0_domain_id, mgmt_api_token)

def get_db(request: Request):
    return request.state.db


ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth2/token", auto_error=False)

def encode_token(body: dict, expires_delta: timedelta = 24*60):
    data = body.copy()
    if data['type'] == "accessToken":
        roles =  auth0.users.list_roles(data['uid']).get('roles',[])
        data['scope'] = [i['name'] for i in roles]
    expire = datetime.utcnow() + timedelta(minutes= expires_delta)
    data.update({"exp": expire })
    encoded_jwt = jwt.encode(data, k.jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str = Depends(oauth2_scheme)):
    if token:
        details = jwt.decode(token, k.jwt_secret  , algorithm=ALGORITHM)
        if details['exp'] < datetime.utcnow() :
            raise HTTPException(status_code=401, detail="Token expired or Invalid")        
        return details
    raise HTTPException(status_code=401, detail="Authorisation Failed")

class TPC:
    def __init__(self, _roles = [], _permissions = [], _token_det = None) -> None:
        self.roles = _roles
        self.permissions = _permissions
        self.token = _token_det

    def __call__(self, token: str = Depends(oauth2_scheme)):
        if self.token:
            token = self.token
        else :
            token = jwt.decode(token, k.jwt_secret, algorith=ALGORITHM)
        if token['exp'] < datetime.utcnow() or token['type'] != "accessToken":
            raise HTTPException(status_code=401, detail="Token expired or Invalid")
        claims = token.get('scope',[])
        for i in self.roles:
            if i in claims:
                return token
        return HTTPException(status_code=403,detail="Operation not Permitted")

        