from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    data: List[T]
    limit: int
    offset: int
