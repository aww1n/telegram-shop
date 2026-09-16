import math


def page_count(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size))


def clamp_page(page: int, total: int, page_size: int) -> int:
    return max(1, min(page, page_count(total, page_size)))
