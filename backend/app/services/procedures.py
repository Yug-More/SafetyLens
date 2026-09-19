from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.procedure import SafetyProcedure
from app.schemas.common import Meta
from app.schemas.procedure import ProcedureRead


def parse_procedure_steps(content: str) -> list[str]:
    steps: list[str] = []
    for line in content.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned[0].isdigit() and "." in cleaned[:4]:
            _, _, rest = cleaned.partition(".")
            steps.append(rest.strip() or cleaned)
        else:
            steps.append(cleaned)
    return steps


def procedure_to_read(procedure: SafetyProcedure) -> ProcedureRead:
    data = ProcedureRead.model_validate(procedure)
    data.steps = parse_procedure_steps(procedure.content)
    return data


def list_procedures(
    db: Session,
    *,
    search: str | None = None,
    category: str | None = None,
    active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ProcedureRead], Meta]:
    query = select(SafetyProcedure)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                SafetyProcedure.title.ilike(pattern),
                SafetyProcedure.procedure_code.ilike(pattern),
                SafetyProcedure.category.ilike(pattern),
            )
        )
    if category:
        query = query.where(SafetyProcedure.category.ilike(f"%{category}%"))
    if active is not None:
        query = query.where(SafetyProcedure.is_active.is_(active))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(SafetyProcedure.title.asc()).limit(limit).offset(offset)
    ).all()
    return [procedure_to_read(row) for row in rows], Meta(
        count=total,
        limit=limit,
        offset=offset,
    )


def get_procedure(db: Session, identifier: str) -> ProcedureRead:
    procedure = db.scalars(
        select(SafetyProcedure).where(
            or_(
                SafetyProcedure.id == identifier,
                SafetyProcedure.procedure_code == identifier,
            )
        )
    ).first()
    if procedure is None:
        raise AppError("NOT_FOUND", "Procedure not found", status_code=404)
    return procedure_to_read(procedure)
