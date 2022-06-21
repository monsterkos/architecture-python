from typing import Protocol, runtime_checkable

from sqlalchemy.orm.session import Session

from domain import model


# duck typing 을 이용한 추상 클래스와 서브 클래스 정의
# ABC 를 상속받지 않아도 required methods 가 정의되어 있는지 여부로 판단
# 상속으로 인한 coupling 을 줄일 수 있음
# super() method 사용할 수 없음
@runtime_checkable
class AbstractRepository(Protocol):
    """
    port : 애플리케이션과 추상화하려는 대상 사이의 인터페이스
    """

    def add(self, batch: model.Batch) -> None:
        ...

    def get(self, reference: str) -> model.Batch:
        ...

    def list(self) -> list[model.Batch]:
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
