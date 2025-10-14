import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Leggi la connessione dal pannello di Render (che la prenderà da Neon)
DATABASE_URL = os.getenv("DATABASE_URL")

# Se vuoi fare test in locale:
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# Crea engine SQLAlchemy
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
