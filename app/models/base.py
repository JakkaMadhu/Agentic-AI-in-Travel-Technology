import peewee
from app.database import db

class BaseModel(peewee.Model):
    class Meta:
        database = db
