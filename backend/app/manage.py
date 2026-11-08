"""Bootstrap an administrator locally; passwords are never command-line arguments."""

import argparse
from getpass import getpass
from app.database.session import init_db, SessionLocal
from app.services.auth import create_user, ROLES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["create-user"])
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", choices=sorted(ROLES), default="administrator")
    args = parser.parse_args()
    password = getpass("Password (12+ characters): ")
    if password != getpass("Confirm password: "):
        parser.error("Passwords differ")
    init_db()
    with SessionLocal() as db:
        create_user(db, args.username, password, args.role)
    print("User created. Sign in through the operator console.")


if __name__ == "__main__":
    main()
