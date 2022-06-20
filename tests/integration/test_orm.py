from domain import model


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        """
        INSERT INTO order_lines (orderid, sku, qty) VALUES
        ('order-001', 'RED-CHAIR', 12),
        ('order-001', 'RED-TABLE', 13),
        ('order-002', 'BLUE-LIPSTICK', 14)
        """
    )
    expected = [
        model.OrderLine("order-001", "RED-CHAIR", 12),
        model.OrderLine("order-001", "RED-TABLE", 13),
        model.OrderLine("order-002", "BLUE-LIPSTICK", 14),
    ]
    assert session.query(model.OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session):
    new_order_line = model.OrderLine("order1", "DECORATIVE-WIDGET", 12)
    session.add(new_order_line)
    session.commit()

    rows = list(session.execute("SELECT orderid, sku, qty FROM 'order_lines'"))
    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]
