from alembic import context
from sqlalchemy import create_engine
from app.core.config import get_settings
from app.database.base import Base
from app import models

config=context.config
target_metadata=Base.metadata

def run_migrations_offline():
    context.configure(url=get_settings().database_url,target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()

def run_migrations_online():
    engine=create_engine(get_settings().database_url)
    with engine.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,render_as_batch=connection.dialect.name=='sqlite')
        with context.begin_transaction():context.run_migrations()

if context.is_offline_mode():run_migrations_offline()
else:run_migrations_online()
