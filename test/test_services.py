import pytest

import model
from repository import FakeRepository
import services


"""
웹 기능에 대한 테스트는 E2E 로 구현하고, 오케스트레이션 관련 테스트는 서비스 계층을 대상으로 한다.
"""


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine("o1", "OMNIOUS-MIRROR", 10)
    batch = model.Batch("b1", "OMNIOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    services.allocate(line, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate(line, repo, session)
    assert batch.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    repo, session = FakeRepository([]), FakeSession()
    line1 = model.OrderLine("o1", "BLUE-PLINTH", 10)
    line2 = model.OrderLine("o2", "BLUE-PLINTH", 5)
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    services.allocate(line1, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate(line2, repo, session)
    assert batch.available_quantity == 90
    services.deallocate(line1, repo, session)
    assert batch.available_quantity == 100
