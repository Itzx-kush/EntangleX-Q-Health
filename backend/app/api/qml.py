from fastapi import APIRouter,Depends
from app.quantum.encoding import QuantumEncodingService
from app.quantum.vqc import VQCService
from app.quantum.qml_schemas import EncodingRequest,EncodingRun,VQCRequest,VQCRun
router=APIRouter(prefix='/api/quantum/qml',tags=['quantum-machine-learning']);_encoding=None;_vqc=None
def encoding_service():
 global _encoding
 if _encoding is None:_encoding=QuantumEncodingService()
 return _encoding
def vqc_service():
 global _vqc
 if _vqc is None:_vqc=VQCService()
 return _vqc
@router.post('/encodings',response_model=EncodingRun,status_code=201)
def encode(p:EncodingRequest,s=Depends(encoding_service)):return s.create(p)
@router.get('/encodings/{run_id}',response_model=EncodingRun)
def get_encoding(run_id:str,s=Depends(encoding_service)):return s.get(run_id)
@router.post('/vqc/train',response_model=VQCRun,status_code=201)
def train_vqc(p:VQCRequest,s=Depends(vqc_service)):return s.train(p)
@router.get('/vqc/{run_id}',response_model=VQCRun)
def get_vqc(run_id:str,s=Depends(vqc_service)):return s.get(run_id)
