from prisma import Prisma


def clear_db():
    db = Prisma()
    db.connect()

    print("Deleting Question Responses...")
    db.questionresponse.delete_many()

    print("Deleting Quiz Attempts...")
    db.quizattempt.delete_many()

    print("Deleting Teacher Action Plans...")
    db.teacheractionplan.delete_many()

    print("Deleting Uploaded Documents...")
    db.uploadeddocument.delete_many()

    print("Deleting Study Twin Matches...")
    db.studytwinmatch.delete_many()

    db.disconnect()
    print("Successfully cleared all application data while keeping Users!")


if __name__ == "__main__":
    clear_db()
