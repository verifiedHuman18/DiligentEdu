from prisma import Prisma


def get_users():
    db = Prisma()
    db.connect()
    users = db.user.find_many(where={"role": "student"})
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Class: {u.class_level}, Subject: {u.subject}")
    db.disconnect()


if __name__ == "__main__":
    get_users()
