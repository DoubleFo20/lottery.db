from datetime import datetime

from pydantic import ConfigDict

from app.schemas.base import BaseSchema


class ImportLogBase(BaseSchema):
    source: str
    import_date: datetime | None = None
    rows_imported: int = 0
    status: str = "pending"
    error_message: str | None = None


class ImportLogCreate(ImportLogBase):
    pass


class ImportLogRead(ImportLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
