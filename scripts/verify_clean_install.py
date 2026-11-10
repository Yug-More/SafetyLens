"""Execute the documented Compose profile on fresh named volumes, never reset data.

Requires free loopback ports3000/8000 and a newly generated private env file.
Rejects any pre-existing project containers/volumes. Leaves artifacts for review.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument("--project", required=True)
p.add_argument("--env-file", required=True, type=Path)
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
if not re.fullmatch(r"safetylens-validation-[a-z0-9-]+", a.project):
    p.error("Use a dedicated safetylens-validation-* project")
for args in [
    [
        "docker",
        "ps",
        "-aq",
        "--filter",
        "label=com.docker.compose.project=" + a.project,
    ],
    [
        "docker",
        "volume",
        "ls",
        "-q",
        "--filter",
        "label=com.docker.compose.project=" + a.project,
    ],
]:
    if subprocess.check_output(args, text=True).strip():
        raise RuntimeError(
            "Project already has containers or volumes; refusing a false clean-install claim"
        )
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
started = time.perf_counter()
subprocess.run(compose + ["up", "--build", "-d"], check=True)
services = []
for _ in range(120):
    services = [
        json.loads(line)
        for line in subprocess.check_output(
            compose + ["ps", "--format", "json"], text=True
        ).splitlines()
        if line.strip()
    ]
    if len(services) == 3 and all(x.get("Health") == "healthy" for x in services):
        break
    time.sleep(1)
else:
    raise RuntimeError("Services failed health checks")
code = "from app.database.session import SessionLocal; from sqlalchemy import text; import json; d=SessionLocal(); print(json.dumps({x:d.execute(text('SELECT count(*) FROM '+x)).scalar() for x in ['cameras','safety_procedures','platform_users']}))"
counts = json.loads(
    subprocess.check_output(
        compose + ["exec", "-T", "backend", "python", "-c", code], text=True
    )
)
if counts["platform_users"] != 0:
    raise RuntimeError("Fresh install unexpectedly has accounts")
result = {
    "project": a.project,
    "no_existing_containers_or_volumes": True,
    "documented_compose_profile": True,
    "all_three_services_healthy": True,
    "first_start_seconds": time.perf_counter() - started,
    "seeded_counts": counts,
    "default_accounts": False,
    "services": [
        {"service": x["Service"], "image": x["Image"], "health": x["Health"]}
        for x in services
    ],
    "limits": [
        "Fresh data volumes and application startup verified; image build cache reused",
        "Loopback HTTP, not production HTTPS",
        "No previous installation reset",
    ],
}
a.output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
