from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_URL = "mysql+pymysql://root:Abs)*m12d31@localhost:3306/image_dedup?charset=utf8mb4"

engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(bind=engine)
