from sqlalchemy.orm import Session


class BaseRepository:
    """Repositories add and flush only. Services call commit() once per operation."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
