from datetime import date
from sqlalchemy.orm.session import Session

from domain import model
from adapters.repository import AbstractRepository

"""
오케스트레이션 : 저장소에서 데이터를 가져오고, 데이터베이스 상태에 따라 입력을 검증하며 오류를 처리하고, DB 에 커밋하는 작업을 포함
데이터의 검증 작업은 웹 API 엔드포인트와는 관련이 없으며, 오케스트레이션은 E2E tests 에서 실제로 테스트해야 되는 대상이 아님
오케스트레이션 계층이나 유스 케이스 계층이라고 부르는 서비스 계층으로 분리
"""


class InvalidSku(Exception):
    ...


def is_valid_sku(sku: str, batches: list[model.Batch]) -> bool:
    return sku in {b.sku for b in batches}


def allocate(line: model.OrderLine, repo: AbstractRepository, session: Session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()
    return batchref


def add_batch(
    ref: str,
    sku: str,
    qty: int,
    eta: date | None,
    repo: AbstractRepository,
    session: Session,
) -> None:
    repo.add(model.Batch(ref, sku, qty, eta))
    session.commit()


def deallocate(
    line: model.OrderLine, repo: AbstractRepository, session: Session
) -> None:
    batches = repo.list()
    model.deallocate(line, batches)
    session.commit()
