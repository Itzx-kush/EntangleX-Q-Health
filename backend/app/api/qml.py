from fastapi import APIRouter, Depends
from app.quantum.encoding import QuantumEncodingService
from app.quantum.vqc import VQCService
from app.quantum.qsvm import QSVMService
from app.quantum.qnn import QNNService
from app.quantum.qml_schemas import EncodingRequest, EncodingRun, VQCRequest, VQCRun, QSVMRequest, QNNRequest, QuantumModelRun, QuantumModelRunList

router = APIRouter(prefix="/api/quantum/qml", tags=["quantum-machine-learning"])
_encoding = None
_vqc = None
_qsvm = None
_qnn = None


def encoding_service():
    global _encoding
    if _encoding is None:
        _encoding = QuantumEncodingService()
    return _encoding


def vqc_service():
    global _vqc
    if _vqc is None:
        _vqc = VQCService()
    return _vqc


def qsvm_service():
    global _qsvm
    if _qsvm is None:
        _qsvm = QSVMService()
    return _qsvm


def qnn_service():
    global _qnn
    if _qnn is None:
        _qnn = QNNService()
    return _qnn


@router.post("/encodings", response_model=EncodingRun, status_code=201)
def encode(payload: EncodingRequest, service=Depends(encoding_service)):
    return service.create(payload)


@router.get("/encodings/{run_id}", response_model=EncodingRun)
def get_encoding(run_id: str, service=Depends(encoding_service)):
    return service.get(run_id)


@router.post("/vqc/train", response_model=VQCRun, status_code=201)
def train_vqc(payload: VQCRequest, service=Depends(vqc_service)):
    return service.train(payload)


@router.get("/vqc/runs")
def list_vqc_runs(encoding_run_id: str | None = None, service=Depends(vqc_service)):
    items = [service._response(record) for record in service.runs.list_vqc(encoding_run_id)]
    return {"items": items, "total": len(items)}


@router.get("/vqc/{run_id}", response_model=VQCRun)
def get_vqc(run_id: str, service=Depends(vqc_service)):
    return service.get(run_id)


@router.post("/qsvm/train", response_model=QuantumModelRun, status_code=201)
def train_qsvm(payload: QSVMRequest, service=Depends(qsvm_service)):
    return service.train(payload)


@router.get("/qsvm/{run_id}", response_model=QuantumModelRun)
def get_qsvm(run_id: str, service=Depends(qsvm_service)):
    return service.get(run_id)


@router.post("/qnn/train", response_model=QuantumModelRun, status_code=201)
def train_qnn(payload: QNNRequest, service=Depends(qnn_service)):
    return service.train(payload)


@router.get("/qnn/{run_id}", response_model=QuantumModelRun)
def get_qnn(run_id: str, service=Depends(qnn_service)):
    return service.get(run_id)


@router.get("/models", response_model=QuantumModelRunList)
def list_quantum_models(encoding_run_id: str | None = None, service=Depends(qsvm_service)):
    records = service.runs.list_models(encoding_run_id)
    items = [service._response(record) if record["model_type"] == "qsvm" else QNNService._response(record) for record in records]
    return {"items": items, "total": len(items)}
