from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from src.telegram_world_bot.config import DBConfig

def create_mysql_engine(db: DBConfig) -> Engine:
    # pool_pre_ping：断线自动恢复；pool_recycle：避免 MySQL wait_timeout 问题
    return create_engine(
        db.sqlalchemy_url(),
        future=True,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

def make_session_factory(db: DBConfig):
    engine = create_mysql_engine(db)
    factory = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False)
    return factory, engine
