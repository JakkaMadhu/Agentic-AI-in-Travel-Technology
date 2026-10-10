import json
import peewee
from app.database import db

class JSONBField(peewee.Field):
    """PostgreSQL JSONB field with automated fallback serialization for SQLite test databases."""
    field_type = "JSONB"

    def db_value(self, value):
        if value is None:
            return None
        db_inst = getattr(getattr(self, "model", None), "_meta", None)
        database = getattr(db_inst, "database", None) if db_inst else db
        if database and hasattr(database, "json_type"):
            return database.json_type(value)
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return value

    def python_value(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value

class BaseModel(peewee.Model):
    class Meta:
        database = db
