from datetime import datetime
import peewee
from app.models.base import BaseModel

class User(BaseModel):
    email = peewee.CharField(unique=True, index=True)
    password_hash = peewee.CharField()
    created_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'users'
