from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base 

from core.config import settings

engine = create_engine(
    settings.DATABASE_URL
)

#debug
with engine.connect() as conn:
    print("Connected!")

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_table():
    #debug
    import models
    Base.metadata.create_all(bind=engine)