from prisma import Prisma


def main() -> None:
    db = Prisma()
    db.connect()

    # Create Mock Users to match the Firebase Auth guide
    db.user.upsert(
        where={"email": "student@diligentedu.com"},
        data={
            "create": {
                "id": "0Z15gOPRLdWCGcf2dricVjOScTI3",
                "email": "student@diligentedu.com",
                "name": "Test Student",
                "role": "student",
                "subject": None,
                "class_level": 10,
            },
            "update": {
                "id": "0Z15gOPRLdWCGcf2dricVjOScTI3",
                "name": "Test Student",
                "role": "student",
                "subject": None,
                "class_level": 10,
            },
        },
    )

    db.user.upsert(
        where={"email": "teacher@diligentedu.com"},
        data={
            "create": {
                "id": "Rk6Abnn5ANQjnhejbUa4poGbvsJ2",
                "email": "teacher@diligentedu.com",
                "name": "Test Teacher",
                "role": "teacher",
                "subject": "science",
            },
            "update": {
                "id": "Rk6Abnn5ANQjnhejbUa4poGbvsJ2",
                "name": "Test Teacher",
                "role": "teacher",
                "subject": "science",
            },
        },
    )

    print("Mock users seeded successfully in Prisma DB.")
    db.disconnect()


if __name__ == "__main__":
    main()
