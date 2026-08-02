from app.models.import_log import ImportLog
from app.repositories.base import CRUDBase
from app.schemas.import_log import ImportLogCreate


class ImportLogRepository(CRUDBase[ImportLog, ImportLogCreate]):
    pass


import_log = ImportLogRepository(ImportLog)
