def get_user_name(user_id: str) -> str:
    from prisma import Prisma

    db = Prisma()
    db.connect()
    user = db.user.find_unique(where={"id": user_id})
    db.disconnect()
    if user and user.name:
        return user.name
    return user_id
