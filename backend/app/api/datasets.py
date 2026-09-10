from __future__ import annotations
from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.core.config import settings
from app.data.errors import DatasetError
from app.data.schemas import DatasetList, DatasetPreview, DatasetSummary, PreviewRequest, TargetSelectionRequest
from app.data.service import DatasetService

router=APIRouter(prefix="/api/datasets",tags=["datasets"])
_service:DatasetService|None=None

def get_dataset_service()->DatasetService:
    global _service
    if _service is None:_service=DatasetService()
    return _service

async def read_limited(file:UploadFile)->bytes:
    max_bytes=settings.max_upload_size_mb*1024*1024
    chunks=[]; total=0
    while chunk:=await file.read(1024*1024):
        total+=len(chunk)
        if total>max_bytes:
            raise DatasetError("FILE_TOO_LARGE","The uploaded file exceeds the configured size limit.",f"Maximum size is {settings.max_upload_size_mb} MB.",413)
        chunks.append(chunk)
    return b"".join(chunks)

@router.post("/upload",response_model=DatasetSummary,status_code=201)
async def upload_dataset(file:UploadFile=File(...),target_column:str|None=Form(default=None),service:DatasetService=Depends(get_dataset_service)):
    content=await read_limited(file)
    return service.ingest(file.filename,content,file.content_type,target_column)

@router.get("",response_model=DatasetList)
def list_datasets(service:DatasetService=Depends(get_dataset_service)):
    items=service.list(); return {"items":items,"total":len(items)}

@router.get("/{dataset_id}",response_model=DatasetSummary)
def get_dataset(dataset_id:str,service:DatasetService=Depends(get_dataset_service)):
    return service.get(dataset_id)

@router.post("/{dataset_id}/target",response_model=DatasetSummary)
def select_target(dataset_id:str,payload:TargetSelectionRequest,service:DatasetService=Depends(get_dataset_service)):
    return service.select_target(dataset_id,payload.target_column)

@router.post("/{dataset_id}/preview",response_model=DatasetPreview)
def preview_dataset(dataset_id:str,payload:PreviewRequest,service:DatasetService=Depends(get_dataset_service)):
    return service.preview(dataset_id,payload.offset,payload.limit)
