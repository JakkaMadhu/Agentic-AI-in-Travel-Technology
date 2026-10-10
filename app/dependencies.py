from typing import Generator
from app.database import db

def get_db() -> Generator:
    """Dependency ensuring safe Peewee connection open/close per request."""
    if db.is_closed():
        db.connect()
    try:
        yield db
    finally:
        if not db.is_closed():
            db.close()
