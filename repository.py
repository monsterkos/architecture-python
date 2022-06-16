from typing import Protocol

from sqlalchemy.orm.session import Session

import model


class AbstractRepository(Protocol):
    """
    port : 애플리케이션과 추상화하려는 대상 사이의 인터페이스
    """

    def add(self, batch: model.Batch) -> None:
        ...

    def get(self, reference: str) -> model.Batch:
        ...


class SqlAlchemyRepository:
    """
    adapter : 인터페이스나 추상화가 뒤에 있는 구현
    """

    def __init__(self, session: Session):
        self.session = session

    def add(self, batch: model.Batch) -> None:
        self.session.add(batch)
        # sql version
        # self.session.execute(
        #     f"""
        #     INSERT INTO batches (reference, sku, _purchased_quantity, eta)
        #     VALUES ('{batch.reference}', '{batch.sku}', '{batch._purchased_quantity}', '{batch.eta}')
        #     """
        # )

    def get(self, reference: str) -> model.Batch:
        return self.session.query(model.Batch).filter_by(reference=reference).one()
        # sql version
        # self.session.execute(
        # f"""
        # SELECT * FROM batches WHERE reference = {reference}
        # """
        # )

    def list(self) -> list[model.Batch]:
        return self.session.query(model.Batch).all()
        # sql version
        # self.session.execute(
        # f"""
        # SELECT * FROM batches
        # """
        # )


class FakeRepository(AbstractRepository):
    """
    adapter
    Test 를 위한 가짜 repository 객체
    가짜 객체를 만들기 어렵다면 추상화를 너무 복잡하게 설계했기 때문이다.
    """

    def __init__(self, batches: list[model.Batch]):
        self._batches = set(batches)

    def add(self, batch: model.Batch):
        self._batches.add(batch)

    def get(self, reference: str) -> model.Batch | None:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> list[model.Batch]:
        return list(self._batches)
