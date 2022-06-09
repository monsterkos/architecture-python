from datetime import datetime

from model import OrderLine, Batch

"""
product(제품) 는 SKU 단위로 식별된다.
customer(고객) 는 order 를 넣는다. order(주문) 는 order reference(주문 참조 번호) 에 의해 식별되며 한 줄 이상의 order line(주문 라인)을 포함한다.
order line 은 고객이 여러 상품을 동시에 주문하는 경우 여러 줄이 생길 수 있다.
각 order line 에는 SKU 와 수량(quantity) 가 있다.
 ex) RED-CHAIR 10 / TASTLESS-LAMP 1

구매 부서는 batch 로 재고를 관리하고 고객의 주문을 처리한다. batch 는 unique ID, SKU, 수량으로 이루어지며 현재 재고의 수량을 알 수 있다.
batch 에 고객의 order line을 할당해야 한다. order line을 batch에 할당하면 해당 batch에 속하는 재고를 고객의 주소로 배송한다.
어떤 batch 의 재고를 order line 에 x 단위로 할당하면 가용 재고 수량은 x 만큼 줄어든다.
ex)
- 20단위의 SMALL-TABLE로 이루어진 batch 가 있고, 2단위의 SMALL-TABLE 을 요구하는 order line 이 있다.
- 주문 라인을 할당하면 배치에 18단위의 SMALL-TABLE 이 남아야 한다.
batch 의 가용 재고 수량이 order line 의 수량보다 작으면 이 order line 을 batch 에 할당할 수 없다.
ex)
- 1단위의 BLUE-CUSHION 이라는 배치가 있고, 2단위의 BLUE-CUSHION 에 대한 order line 이 있다.
- 이 order line 을 batch 에 할당해서는 안된다.

같은 order line 을 두 번 이상 할당해서는 안 된다.
ex)
- 10단위의 RED-VASE 라는 batch 가 있고, 2단위의 RED-VASE order line 을 batch 에 할당한다.
- 같은 order line 을 다시 같은 batch 에 할당해도 batch 의 가용 재고 수량은 계속 8개를 유지해야 한다.

batch 가 현재 배송 중이면 ETA(Estimated Time of Arrival) 정보가 batch 에 들어있다. ETA 가 없는 batch 는 창고 재고다. 창고 재고를
배송 중인 batch 보다 먼저 할당해야 한다. 배송 중인 batch 를 할당할 때는 ETA 가 가장 빠른 batch 를 먼저 할당한다.

할당된 order line 을 해제할 수 있으며, 할당되지 않은 order_line 을 해제하면 batch의 가용 수량에 아무 영향이 없어야 한다.
"""


def make_temp_batch_and_order_line(
    sku: str, batch_qty: int, order_qty: int
) -> tuple[Batch, OrderLine]:
    return Batch(sku, batch_qty, eta=datetime.now()), OrderLine(sku=sku, qty=order_qty)


class TestAllocation:
    @staticmethod
    def test_allocating_to_a_batch_reduces_the_available_quantity():
        batch, order_line = make_temp_batch_and_order_line("SMALL-TABLE", 20, 2)

        batch.allocate(order_line)

        assert batch.available_quantity == 18

    @staticmethod
    def test_cannot_allocate_if_available_smaller_than_required():
        batch, order_line = make_temp_batch_and_order_line("BLUE-CUSHION", 1, 2)

        assert batch.can_allocate(order_line) is False
        assert batch.available_quantity == 1

    @staticmethod
    def test_do_not_allocate_same_order_line_twice():
        batch, order_line = make_temp_batch_and_order_line("RED-VASE", 10, 2)

        batch.allocate(order_line)
        batch.allocate(order_line)

        assert batch.available_quantity == 8

    @staticmethod
    def test_can_allocate_if_available_greater_than_required():
        batch, order_line = make_temp_batch_and_order_line("ELEGANT-LAMP", 3, 1)

        assert batch.can_allocate(order_line)

    @staticmethod
    def test_can_allocate_if_available_equal_to_required():
        batch, order_line = make_temp_batch_and_order_line("ELEGANT-LAMP", 3, 3)

        assert batch.can_allocate(order_line)

    @staticmethod
    def test_cannot_allocate_if_sku_do_not_match():
        batch = Batch("BIG-DESK", 10)
        order_line = OrderLine(sku="SMALL-DESK", qty=2)

        assert batch.can_allocate(order_line) is False

    @staticmethod
    def test_can_only_deallocate_allocated_line():
        batch, order_line = make_temp_batch_and_order_line("ELEGANT-LAMP", 3, 3)
        batch.deallocate(order_line)

        assert batch.available_quantity == 3
