from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Meta(APIModel):
    count: int
    limit: int
    offset: int


class ItemResponse(APIModel, Generic[T]):
    data: T


class CollectionResponse(APIModel, Generic[T]):
    data: list[T]
    meta: Meta


class PaginationParams(APIModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def require_non_blank(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("must not be blank")
    return cleaned


class NonBlankStr(str):
    @classmethod
    def __get_validators__(cls):  # pragma: no cover - legacy hook
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        return require_non_blank(value)


class SearchQuery(APIModel):
    search: str | None = None

    @field_validator("search")
    @classmethod
    def clean_search(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
