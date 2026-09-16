from decimal import Decimal, InvalidOperation


def positive_decimal(value: str) -> Decimal:
    try:
        number = Decimal(value.replace(" ", "").replace(",", "."))
    except InvalidOperation as error:
        raise ValueError("Введите число, например 4500") from error
    if number < 0:
        raise ValueError("Значение не может быть отрицательным")
    return number.quantize(Decimal("0.01"))


def non_negative_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise ValueError("Введите целое число") from error
    if number < 0:
        raise ValueError("Значение не может быть отрицательным")
    return number
