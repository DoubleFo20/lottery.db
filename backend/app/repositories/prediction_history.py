from app.models.prediction_history import PredictionHistory
from app.repositories.base import CRUDBase
from app.schemas.prediction_history import PredictionHistoryCreate


class PredictionHistoryRepository(CRUDBase[PredictionHistory, PredictionHistoryCreate]):
    pass


prediction_history = PredictionHistoryRepository(PredictionHistory)
