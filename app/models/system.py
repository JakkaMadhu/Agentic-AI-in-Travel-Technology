from datetime import datetime
import peewee
from app.models.base import BaseModel, JSONBField
from app.models.travel import TripSession

class ApiLog(BaseModel):
    session = peewee.ForeignKeyField(TripSession, backref="api_logs", on_delete="CASCADE")
    service_name = peewee.CharField(index=True)
    endpoint = peewee.CharField()
    request_payload = JSONBField(null=True)
    response_payload = JSONBField(null=True)
    status_code = peewee.IntegerField()
    latency_ms = peewee.IntegerField()
    created_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "api_logs"
