from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import APIModel, require_non_blank


class ProcedureRead(APIModel):
    id: str
    procedure_code: str
    title: str
    category: str
    version: str
    content: str
    source_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    steps: list[str] = Field(default_factory=list)


class ProcedureCreate(APIModel):
    procedure_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=32)
    content: str = Field(min_length=1)
    source_name: str = Field(min_length=1, max_length=200)
    is_active: bool = True

    @field_validator("procedure_code", "title", "category", "version", "content", "source_name")
    @classmethod
    def not_blank(cls, value: str) -> str:
        return require_non_blank(value)
