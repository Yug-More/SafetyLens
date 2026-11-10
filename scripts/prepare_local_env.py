"""Create first-run local secrets without overwriting an existing environment."""

import argparse
import base64
import os
from pathlib import Path
import secrets

p = argparse.ArgumentParser()
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
content = (
    "\n".join(
        [
            "POSTGRES_PASSWORD=" + secrets.token_urlsafe(32),
            "CAMERA_ENCRYPTION_KEY="
            + base64.urlsafe_b64encode(os.urandom(32)).decode(),
            "DETECTOR_API_TOKEN=" + secrets.token_urlsafe(32),
            "DETECTOR_CAMERA_IDS=cam-03",
            "MAX_REQUEST_SIZE_MB=110",
        ]
    )
    + "\n"
)
fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as handle:
    handle.write(content)
print(
    "Created private environment file; no values printed. Bootstrap an administrator interactively."
)
