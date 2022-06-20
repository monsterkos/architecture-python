from domain import model
from adapters import repository


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        "SELECT reference, sku, _purchased_quantity, eta FROM 'batches'"
    )
    assert list(rows) == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def insert_order_line(session) -> int:
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES ("order1", "GENERIC-SOFA", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA"),
    )
    return orderline_id


def insert_batch(session, reference: str) -> int:
    session.execute(
        f"""
        INSERT INTO batches (reference, sku, _purchased_quantity, eta)
        VALUES ("{reference}", "GENERIC-SOFA", 100, NULL)
        """
    )
    [[batch_id]] = session.execute(
        f"SELECT id FROM batches WHERE reference ='{reference}' AND sku = 'GENERIC-SOFA'"
    )
    return batch_id


def insert_allocation(session, batch_id: int, orderline_id: int) -> None:
    session.execute(
        f"""
        INSERT INTO allocations (orderline_id, batch_id)
        VALUES ("{orderline_id}", "{batch_id}")
        """
    )


def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, "batch1")
    insert_batch(session, "batch2")
    insert_allocation(session, batch1_id, orderline_id)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get("batch1")

    expected = model.Batch("batch1", "GENERIC-SOFA", 100, eta=None)
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocated_orders == {
        model.OrderLine("order1", "GENERIC-SOFA", 12)
    }


def test_adapters_are_subclass_of_port():
    assert isinstance(repository.SqlAlchemyRepository, repository.AbstractRepository)
    assert isinstance(repository.FakeRepository, repository.AbstractRepository)
