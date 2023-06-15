from fastapi import Depends, FastAPI, HTTPException, Request, Response

from .db import setup, orm
from .routes import users, oauth2

orm.Base.metadata.create_all(bind=setup.engine)

app = FastAPI()
app.include_router(users.router)
app.include_router(oauth2.router)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = setup.SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response