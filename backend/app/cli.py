import argparse
import getpass
import sys

from sqlalchemy import func

from app.db.auth_store import AuthSessionLocal, UserCredential, init_auth_db
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def set_password(email: str) -> int:
    normalized_email = email.strip().lower()
    init_auth_db()

    db = SessionLocal()
    try:
        user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
        if user is None:
            print("No account exists with that email address.", file=sys.stderr)
            return 1
        if not user.is_active:
            print("The account is inactive; activate it before setting a password.", file=sys.stderr)
            return 1
        user_id = user.id
        stored_email = user.email.strip().lower()
    finally:
        db.close()

    password = getpass.getpass("New password (8-128 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 8 or len(password) > 128:
        print("Password must be between 8 and 128 characters.", file=sys.stderr)
        return 1
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    auth_db = AuthSessionLocal()
    try:
        credential = auth_db.query(UserCredential).filter_by(user_id=user_id).first()
        if credential is None:
            credential = UserCredential(email=stored_email, user_id=user_id, password_hash=hash_password(password))
            auth_db.add(credential)
        else:
            credential.email = stored_email
            credential.password_hash = hash_password(password)
        auth_db.commit()
    except Exception:
        auth_db.rollback()
        raise
    finally:
        auth_db.close()

    print(f"Password set for {stored_email}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="fitdesk")
    commands = parser.add_subparsers(dest="command", required=True)
    password_command = commands.add_parser("set-password", help="Set a password for an existing active account")
    password_command.add_argument("email")
    arguments = parser.parse_args()

    if arguments.command == "set-password":
        return set_password(arguments.email)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())