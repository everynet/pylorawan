import typing

from .interface import DataRate


def get_range_datarates(table_datarates: typing.Dict[int, DataRate], start: int, end: int) -> typing.List[DataRate]:
    return [table_datarates[i] for i in range(start, end)]
