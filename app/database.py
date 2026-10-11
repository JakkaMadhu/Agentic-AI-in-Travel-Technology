from playhouse.db_url import parse as parse_db_url
from playhouse.postgres_ext import PostgresqlExtDatabase
from app.config import settings

def create_database_client() -> PostgresqlExtDatabase:
    """Initialize PostgreSQL client exclusively through DATABASE_URL."""
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL must be set in environment configuration.")

    db_config = parse_db_url(settings.DATABASE_URL)
    if "sslmode" not in db_config and "localhost" not in settings.DATABASE_URL:
        db_config["sslmode"] = "require"
    db_config["autorollback"] = True
    db_config["connect_timeout"] = 10
    db_config["keepalives"] = 1
    db_config["keepalives_idle"] = 30
    db_config["keepalives_interval"] = 10
    db_config["keepalives_count"] = 5

    return PostgresqlExtDatabase(**db_config)

db = create_database_client()

def init_db():
    """Ensure database connection and schema tables exist."""
    from app.models.user import User
    from app.models.travel import TripSession
    from app.models.system import ApiLog
    db.connect(reuse_if_open=True)
    db.create_tables([User, TripSession, ApiLog], safe=True)
