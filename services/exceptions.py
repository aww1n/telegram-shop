class ShopError(Exception):
    """Safe domain error which may be shown to a user."""


class ProductUnavailable(ShopError):
    """Requested product cannot be purchased."""


class InsufficientStock(ShopError):
    def __init__(self, available: int) -> None:
        self.available = available
        super().__init__(f"Доступно только {available} шт.")


class EmptyCart(ShopError):
    """Checkout was requested for an empty cart."""
