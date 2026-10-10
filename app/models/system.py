from datetime import datetime
import peewee
from playhouse.postgres_ext import JSONField
from app.models.base import BaseModel
from app.models.travel import TripSession

class ApiLog(BaseModel):
    session = peewee.ForeignKeyField(TripSession, backref='api_logs', on_delete='CASCADE')
    service_name = peewee.CharField(index=True)
    endpoint = peewee.CharField()
    request_payload = JSONField(null=True)
    response_payload = JSONField(null=True)
    status_code = peewee.IntegerField()
    latency_ms = peewee.IntegerField()
    created_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'api_logs'
