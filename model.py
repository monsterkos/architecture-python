import uuid
from dataclasses import dataclass
from datetime import date


# 값 객체 (value object) : 내부 데이터에 따라 식별되는 도메인 객체
@dataclass(
    frozen=True
)  # frozen=True 로 해당 객체를 불변 객체로 만들어주며, dict 키로 사용할 수 있고 set 에 add 할 수 있다.
class OrderLine:
    sku: str
    qty: int
    order_id: str = str(uuid.uuid4())


# 엔티티 (entity) : 일부 값이 바뀌어도 특정 식별 값에 의해 동일하다고 판단할 수 있는 영속적인 정체성을 갖는 도메인 객체
class Batch:
    def __init__(self, sku: str, qty: int, eta: date | None = None):
        self.ref: str = str(uuid.uuid4())
        self.sku = sku
        self.purchased_quantity = qty
        self.eta = eta
        self._allocated_orders: set[OrderLine] = set()

    def __repr__(self):
        return f"Batch {self.ref}"

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return self.ref == other.ref

    def __hash__(self):
        return hash(self.ref)

    # sorted() 함수를 사용하기 위해서 __gt__ 메서드가 구현되어야 함
    # eta=None 이 가장 우선하며, 날짜가 빠를수록 먼저 할당된다는 도메인의 의미 표현
    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def allocate(self, order_line: OrderLine) -> None:
        if self.can_allocate(order_line):
            self._allocated_orders.add(order_line)

    def can_allocate(self, order_line: OrderLine) -> bool:
        return self.sku == order_line.sku and self.available_quantity >= order_line.qty

    def deallocate(self, order_line: OrderLine) -> None:
        if order_line.order_id in self._allocated_orders:
            self._allocated_orders.remove(order_line)

    @property
    def available_quantity(self) -> int:
        return self.purchased_quantity - self.allocated_quantity

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocated_orders)


# 여러 배치를 인자로 받는 allocate 함수 생성
def allocate(order_line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(order_line))
        batch.allocate(order_line)
    except StopIteration as e:
        raise OutOfStock(f"Out of stock for sku {order_line.sku}") from e
    return batch.ref


class OutOfStock(Exception):
    ...
