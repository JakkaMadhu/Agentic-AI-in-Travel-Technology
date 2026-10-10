from datetime import datetime
import peewee
from app.models.base import BaseModel, JSONBField
from app.models.user import User

class TripSession(BaseModel):
    user = peewee.ForeignKeyField(User, backref="trips", on_delete="CASCADE")
    session_uuid = peewee.CharField(unique=True, index=True)
    user_query = peewee.TextField()
    status = peewee.CharField(default="PENDING")
    parsed_intent = JSONBField(null=True)
    final_plan = JSONBField(null=True)
    created_at = peewee.DateTimeField(default=datetime.utcnow)
    updated_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "trip_sessions"
