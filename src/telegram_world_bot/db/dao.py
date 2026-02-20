# 作者：Alex
# 2026/1/28 16:52
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import delete

from src.telegram_world_bot.db.models import IdempotencyKey, EventLog

class MySQLDAO:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def try_acquire_idempotency(self, key: str) -> bool:
        with self._session_factory() as session:  # type: Session
            session.add(IdempotencyKey(key=key))
            try:
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                return False

    def log_event(self, user_id: int, event: str, payload: str | None = None) -> None:
        with self._session_factory() as session:  # type: Session
            session.add(EventLog(user_id=user_id, event=event, payload=payload))
            session.commit()

    def clear_idempotency_keys(self) -> int:
        with self._session_factory() as session:  # type: Session
            result = session.execute(delete(IdempotencyKey))
            session.commit()
            return int(result.rowcount or 0)