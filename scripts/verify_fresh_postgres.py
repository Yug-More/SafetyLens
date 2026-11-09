"""Migrate and seed a new isolated PostgreSQL DB; never overwrite existing data."""

import argparse
import json
from pathlib import Path
import subprocess
import uuid

p = argparse.ArgumentParser()
p.add_argument("--env-file", required=True, type=Path)
p.add_argument("--project", default="safetylens-hardening")
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
compose = [
    "docker",
    "compose",
    "--env-file",
    str(a.env_file),
    "-p",
    a.project,
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.postgres.yml",
]
name = "research_fresh_" + uuid.uuid4().hex[:8]
subprocess.run(
    compose + ["exec", "-T", "postgres", "createdb", "-U", "safetylens", name],
    check=True,
)
code = """import os,subprocess,json,sys
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine,text
name=sys.argv[1]
env={**os.environ,'DATABASE_URL':make_url(os.environ['DATABASE_URL']).set(database=name).render_as_string(hide_password=False)}
subprocess.run(['python','-m','alembic','-c','alembic.ini','upgrade','head'],env=env,check=True,capture_output=True)
subprocess.run(['python','-m','app.seed.run'],env=env,check=True,capture_output=True)
engine=create_engine(env['DATABASE_URL'])
with engine.connect() as db:
 result={x:int(db.execute(text('SELECT count(*) FROM '+x)).scalar()) for x in ['cameras','safety_procedures','procedure_chunks']}
 result['migration_revision']=db.execute(text('SELECT version_num FROM alembic_version')).scalar()
print(json.dumps(result))
"""
result = subprocess.run(
    compose + ["exec", "-T", "backend", "python", "-c", code, name],
    capture_output=True,
    text=True,
    check=True,
)
output = json.loads(result.stdout)
output.update(
    database="new dedicated verification database", existing_database_untouched=True
)
a.output.write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(output))
