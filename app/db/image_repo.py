from sqlalchemy import text
from db.session import SessionLocal


def get_image_by_md5(md5: str):
    session = SessionLocal()
    try:
        sql = text("SELECT * FROM image_library WHERE md5 = :md5 LIMIT 1")
        return session.execute(sql, {"md5": md5}).fetchone()
    finally:
        session.close()

