import uuid
from pydantic import BaseModel
from datetime import datetime

from exception import LackOfQuantity


class OrderLine(BaseModel):
    order_id: str = str(uuid.uuid4())
    sku: str
    quantity: int


class Batch:
    def __init__(self, sku: str, quantity: int, eta: datetime | None = None):
        self.ref: str = str(uuid.uuid4())
        self.sku = sku
        self.available_quantity = quantity
        self.eta = eta
        self._allocated_orders: set[OrderLine.order_id] = set()

    def __repr__(self):
        return f"Batch {self.ref}"

    def allocate(self, order_line: OrderLine) -> None:
        if self.available_quantity < order_line.quantity:
            raise LackOfQuantity(
                f"Available Quantity of {self.sku} is lower than order quantity"
            )

        if order_line.order_id in self._allocated_orders:
            return

        self.available_quantity -= order_line.quantity
        self._allocated_orders.add(order_line.order_id)
