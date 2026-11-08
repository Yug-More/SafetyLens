"""Back up isolated Compose evidence and restore it into a NEW verification volume.

Never extracts into the running application's data volume. Archive contains
sensitive media and is created mode0600 outside Git. Run only on a test project.
"""

import argparse, hashlib, json, os, subprocess, uuid
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--env-file", required=True)
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
compose = [
    "docker",
    "compose",
    "--env-file",
    a.env_file,
    "-p",
    "safetylens-hardening",
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.postgres.yml",
]
archive = a.output / "media.tar"
fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as handle:
    subprocess.run(
        compose
        + [
            "exec",
            "-T",
            "backend",
            "tar",
            "-C",
            "/data",
            "-cf",
            "-",
            "uploads",
            "frames",
            "reports",
            "procedures",
        ],
        stdout=handle,
        check=True,
    )
manifest_code = """import hashlib,json; from pathlib import Path
root=Path('/data'); print(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for kind in ['uploads','frames','reports','procedures'] for p in (root/kind).rglob('*') if p.is_file()}))"""
original = json.loads(
    subprocess.check_output(
        compose + ["exec", "-T", "backend", "python", "-c", manifest_code]
    )
)
volume = "safetylens-restore-" + uuid.uuid4().hex[:12]
restore_code = """import sys,tarfile,json,hashlib; from pathlib import Path
root=Path('/restore')
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as tar:
 for item in tar:
  if not (root/item.name).resolve().is_relative_to(root): raise RuntimeError('Unsafe archive path')
  tar.extract(item,root,filter='data')
print(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}))"""
with archive.open("rb") as handle:
    restored = json.loads(
        subprocess.check_output(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--user",
                "0:0",
                "-v",
                volume + ":/restore",
                "safetylens-hardening-backend",
                "python",
                "-c",
                restore_code,
            ],
            stdin=handle,
        )
    )
assert original == restored
result = {
    "files": len(original),
    "archive_bytes": archive.stat().st_size,
    "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "all_file_hashes_preserved": True,
    "archive_mode": oct(archive.stat().st_mode & 0o777),
    "restore_volume": volume,
    "scope": "Isolated local evidence restoration, not encrypted offsite/disaster recovery",
}
(a.output / "verification.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
