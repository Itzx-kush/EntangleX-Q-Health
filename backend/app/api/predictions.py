from fastapi import APIRouter, Depends
from app.prediction.schemas import PredictionList, PredictionRecord, PredictionRequest
from app.prediction.service import PredictionService
router = APIRouter(prefix="/api/predictions", tags=["prediction-decision-support"])
_service = None
def get_prediction_service():
    global _service
    if _service is None:
        _service = PredictionService()
    return _service
@router.post("", response_model=PredictionRecord, status_code=201)
def predict(payload: PredictionRequest, service=Depends(get_prediction_service)):
    return service.predict(payload)
@router.get("", response_model=PredictionList)
def list_predictions(model_run_id: str | None = None, service=Depends(get_prediction_service)):
    items = service.list(model_run_id)
    return {"items": items, "total": len(items)}
@router.get("/{prediction_id}", response_model=PredictionRecord)
def get_prediction(prediction_id: str, service=Depends(get_prediction_service)):
    return service.get(prediction_id)
