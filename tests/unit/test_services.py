import pytest
from datetime import datetime, timedelta

from domain import model
from service_layer import services

"""
웹 기능에 대한 테스트는 E2E 로 구현하고, 오케스트레이션 관련 테스트는 서비스 계층을 대상으로 한다.
"""


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeRepository:
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


def test_returns_allocation():
    # line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    # batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, repo, session)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
    assert result == "b1"


def test_error_for_invalid_sku():
    # line = model.OrderLine("o1", "NONEXISTSKU", 10)
    # batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTSKU"):
        services.allocate("o1", "NONEXISTSKU", 10, repo, FakeSession())


def test_commits():
    # line = model.OrderLine("o1", "OMNIOUS-MIRROR", 10)
    # batch = model.Batch("b1", "OMNIOUS-MIRROR", 100, eta=None)
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "OMNIOUS-MIRROR", 100, None, repo, session)

    services.allocate("o1", "OMNIOUS-MIRROR", 10, repo, session)
    assert session.committed is True


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    # line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)
    assert batch.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    repo, session = FakeRepository([]), FakeSession()
    # line1 = model.OrderLine("o1", "BLUE-PLINTH", 10)
    # line2 = model.OrderLine("o2", "BLUE-PLINTH", 5)
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate("o2", "BLUE-PLINTH", 5, repo, session)
    assert batch.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)
    assert batch.available_quantity == 100


today = datetime.today()
tomorrow = datetime.today() + timedelta(days=1)
later = datetime.today() + timedelta(days=5)


def test_prefers_warehouse_batches_to_shipments():
    """
    test_batches(도메인 계층 테스트) > test_prefers_current_stock_batches_to_shipments 를 서비스 계층 테스트로 재작성
    이유 : 도메인 계층의 테스트를 지나치게 많이 하면, 설계의 변화에 따라 수정해야 할 테스트가 너무 많아져 유지보수가 어렵다.
    서비스 계층에 대한 테스트만 수행하여 직접 모델 객체의 속성이나 메서드가 테스트와 상호작용하는 것을 줄이면 자유롭게 모델 객체를 리팩터링 할 수 있다.
    """
    # in_stock_batch = model.Batch("batch-001", "RETRO-CLOCK", 100)
    # shipment_batch = model.Batch("batch-002", "RETRO-CLOCK", 100, eta=tomorrow)
    # repo = FakeRepository([in_stock_batch, shipment_batch])
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch-001", "RETRO-CLOCK", 100, None, repo, session)
    services.add_batch("batch-002", "RETRO-CLOCK", 100, tomorrow, repo, session)

    services.allocate("order-001", "RETRO-CLOCK", 10, repo, session)

    assert repo.get("batch-001").available_quantity == 90
    assert repo.get("batch-002").available_quantity == 100


def test_add_batch():
    """
    기존 서비스 계층 테스트에서 도메인 객체인 Batch 를 import 하여 생성하고 이를 가짜 저장소에 저장하던 과정을 add_batch 함수를 통해 없앨 수 있다.
    이로써 서비스 계층의 모든 테스트에서 도메인 모델에 대한 의존성을 없앨 수 있다.
    """
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed
