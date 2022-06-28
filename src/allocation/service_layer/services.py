from datetime import date

from ..domain import model
from .unit_of_work import AbstractUnitOfWork

"""
오케스트레이션 : 저장소에서 데이터를 가져오고, 데이터베이스 상태에 따라 입력을 검증하며 오류를 처리하고, DB 에 커밋하는 작업을 포함
데이터의 검증 작업은 웹 API 엔드포인트와는 관련이 없으며, 오케스트레이션은 E2E tests 에서 실제로 테스트해야 되는 대상이 아님
오케스트레이션 계층이나 유스 케이스 계층이라고 부르는 서비스 계층으로 분리
"""


class InvalidSku(Exception):
    ...


def is_valid_sku(sku: str, batches: list[model.Batch]) -> bool:
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    """
    도메인으로부터 완전히 분리된 서비스 계층을 만들기 위해 도메인 객체(OrderLine) 가 아닌 원시 타입을 파라미터로 받음
    """
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = model.allocate(line, batches)
        uow.commit()
    return batchref


def add_batch(
    ref: str, sku: str, qty: int, eta: date | None, uow: AbstractUnitOfWork
) -> None:
    with uow:
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()


def deallocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> None:
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        model.deallocate(line, batches)
        uow.commit()
