from decimal import Decimal


def plain_decimal(value: Decimal | None) -> str | None:
    """Drop the column's scale padding — 49000.0000000000 reads as 49000.

    ``format(..., "f")`` rather than ``str`` because ``normalize`` turns small
    and round numbers into 1E-8 and 1E+3, which clients cannot parse.
    """
    if value is None:
        return None

    return format(value.normalize(), "f")
