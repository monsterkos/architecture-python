from typing import Protocol

from sqlalchemy.orm.session import Session

import model


class AbstractRepository(Protocol):
    def add(self, batch: model.Batch) -> None:
        ...

    def get(self, reference: str) -> model.Batch:
        ...


class SqlAlchemyRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch: model.Batch) -> None:
        self.session.add(batch)

    def get(self, reference: str) -> model.Batch:
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self) -> list[model.Batch]:
        return self.session.query(model.Batch).all()
