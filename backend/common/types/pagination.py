from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

T = TypeVar('T')


@dataclass
class PaginatedResult(Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    page_size: int
