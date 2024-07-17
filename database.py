from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends, Cookie
from sqlalchemy.orm import Session
from uuid import uuid4
from models import User

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(session_id: str = Cookie(None), db: Session = Depends(get_db)):
    if not session_id:
        session_id = str(uuid4())
        user = User(session_id=session_id)
        db.add(user)
        db.commit()
    else:
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            user = User(session_id=session_id)
            db.add(user)
            db.commit()
    return user, session_id