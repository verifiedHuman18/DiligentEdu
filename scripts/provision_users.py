import csv
import os
import sys

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import AlreadyExistsError

from backend.auth.firebase_auth import init_firebase
from prisma import Prisma


def provision_users(csv_path: str):
    print("Initializing Firebase...")
    init_firebase()

    print("Connecting to Prisma DB...")
    db = Prisma()
    db.connect()

    success_count = 0
    error_count = 0

    print(f"Reading CSV file: {csv_path}\n")
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row["email"].strip()
            password = row["password"].strip()
            name = row["name"].strip()
            role = row["role"].strip()
            subject = row.get("subject", "").strip() or None

            try:
                # 1. Create User in Firebase
                try:
                    user_record = firebase_auth.create_user(
                        email=email, password=password, display_name=name
                    )
                    uid = user_record.uid
                    print(f"Created Firebase user: {email} (UID: {uid})")
                except AlreadyExistsError:
                    # If user already exists in Firebase, fetch their UID
                    user_record = firebase_auth.get_user_by_email(email)
                    uid = user_record.uid
                    print(f"Firebase user already exists: {email} (UID: {uid})")

                # Parse class_level safely
                class_level_val = None
                if row.get("class_level") and row["class_level"].strip().isdigit():
                    class_level_val = int(row["class_level"].strip())

                # 2. Upsert in Prisma
                db.user.upsert(
                    where={"email": email},
                    data={
                        "create": {
                            "id": uid,
                            "email": email,
                            "name": name,
                            "role": role,
                            "subject": subject,
                            "class_level": class_level_val,
                        },
                        "update": {
                            "id": uid,
                            "name": name,
                            "role": role,
                            "subject": subject,
                            "class_level": class_level_val,
                        },
                    },
                )
                print(f"Upserted Prisma user: {email}\n")
                success_count += 1

            except Exception as e:
                print(f"Error provisioning {email}: {e}")
                error_count += 1

    db.disconnect()
    print(f"Provisioning complete. Success: {success_count}, Errors: {error_count}")


if __name__ == "__main__":
    csv_file_path = os.path.join(PROJECT_ROOT, "data", "users.csv")
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        sys.exit(1)

    provision_users(csv_file_path)
