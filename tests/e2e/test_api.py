import uuid
import pytest
import requests

import config


def random_hex() -> str:
    return uuid.uuid4().hex[:6]


def random_sku(name: str | int = "") -> str:
    return f"sku-{name}-{random_hex()}"


def random_batchref(name: str | int = "") -> str:
    return f"batch-{name}-{random_hex()}"


def random_orderid(name: str | int = "") -> str:
    return f"order-{name}-{random_hex()}"


@pytest.mark.usefixtures("restart_api")
def test_api_returns_allocation():
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    post_to_add_batch(laterbatch, sku, 100, "2022-06-16")
    post_to_add_batch(earlybatch, sku, 100, "2022-06-15")
    post_to_add_batch(otherbatch, othersku, 100, None)
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
def test_allocations_are_persisted():
    sku = random_sku()
    batch1, batch2 = random_batchref(1), random_batchref(2)
    order1, order2 = random_orderid(1), random_orderid(2)
    post_to_add_batch(batch1, sku, 10, "2022-06-01")
    post_to_add_batch(batch2, sku, 10, "2022-06-02")
    line1 = {"orderid": order1, "sku": sku, "qty": 10}
    line2 = {"orderid": order2, "sku": sku, "qty": 10}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=line1)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch1

    r = requests.post(f"{url}/allocate", json=line2)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch2


"""
E2E 에서는 예외 사항에 대한 모든 테스트가 필요 없이, 정상과 비정상 경로만 테스트한다.
"""


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_201_and_allocated_batch():
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    post_to_add_batch(laterbatch, sku, 100, "2022-06-02")
    post_to_add_batch(earlybatch, sku, 100, "2022-06-01")
    post_to_add_batch(otherbatch, othersku, 100, None)
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 10}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"


@pytest.mark.usefixtures("restart_api")
def test_deallocate():
    sku = random_sku()
    batch = random_batchref()
    post_to_add_batch(batch, sku, 100, "2022-06-02")
    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch
    r = requests.post(f"{url}/deallocate", json=data)
    assert r.status_code == 200


def post_to_add_batch(ref, sku, qty, eta):
    """
    batch 를 추가하는 api 를 통해서 기존 conftest.py 의 add_stock 을 대체할 수 있다.
    """
    url = config.get_api_url()
    r = requests.post(
        f"{url}/batch", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    assert r.status_code == 201
