from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config

# Use the database path from config
engine = create_engine(f'sqlite:///{Config.DATABASE_PATH}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()