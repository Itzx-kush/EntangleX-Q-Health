from __future__ import annotations
import logging
from time import perf_counter
from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.data.errors import DatasetError
from app.data.schemas import DatasetList, DatasetPreview, DatasetSummary, PreviewRequest, TargetSelectionRequest
from app.data.service import DatasetService

logger=logging.getLogger(__name__)
router=APIRouter(prefix="/api/datasets",tags=["datasets"])
_service:DatasetService|None=None

def get_dataset_service()->DatasetService:
    global _service
    if _service is None:_service=DatasetService()
    return _service

async def read_limited(file:UploadFile)->bytes:
    max_bytes=settings.max_upload_size_mb*1024*1024
    chunks=[];total=0
    while chunk:=await file.read(1024*1024):
        total+=len(chunk)
        if total>max_bytes:
            raise DatasetError("FILE_TOO_LARGE","The uploaded file exceeds the configured size limit.",f"Maximum size is {settings.max_upload_size_mb} MB.",413)
        chunks.append(chunk)
    return b"".join(chunks)

@router.post("/upload",response_model=DatasetSummary,status_code=201)
async def upload_dataset(file:UploadFile=File(...),target_column:str|None=Form(default=None),service:DatasetService=Depends(get_dataset_service)):
    started=perf_counter();safe_name=(file.filename or "unnamed")[:255]
    logger.info("dataset_upload_received filename=%r content_type=%r",safe_name,file.content_type)
    try:
        read_started=perf_counter();content=await read_limited(file);read_seconds=perf_counter()-read_started
        logger.info("dataset_upload_read filename=%r size_bytes=%d read_seconds=%.6f",safe_name,len(content),read_seconds)
        # Pandas/openpyxl parsing, profiling and SQLite writes are synchronous.
        # Keep them off the ASGI event loop so health/error responses remain available.
        result=await run_in_threadpool(service.ingest,file.filename,content,file.content_type,target_column)
        logger.info("dataset_upload_completed dataset_id=%s filename=%r size_bytes=%d total_seconds=%.6f",result["id"],safe_name,len(content),perf_counter()-started)
        return result
    except DatasetError as exc:
        logger.warning("dataset_upload_failed filename=%r code=%s total_seconds=%.6f",safe_name,exc.code,perf_counter()-started)
        raise
    except Exception as exc:
        logger.exception("dataset_upload_failed filename=%r exception_type=%s total_seconds=%.6f",safe_name,type(exc).__name__,perf_counter()-started)
        raise
    finally:
        await file.close()

@router.get("",response_model=DatasetList)
def list_datasets(service:DatasetService=Depends(get_dataset_service)):
    items=service.list();return {"items":items,"total":len(items)}
@router.get("/{dataset_id}",response_model=DatasetSummary)
def get_dataset(dataset_id:str,service:DatasetService=Depends(get_dataset_service)):return service.get(dataset_id)
@router.post("/{dataset_id}/target",response_model=DatasetSummary)
def select_target(dataset_id:str,payload:TargetSelectionRequest,service:DatasetService=Depends(get_dataset_service)):return service.select_target(dataset_id,payload.target_column,payload.task_type)
@router.post("/{dataset_id}/preview",response_model=DatasetPreview)
def preview_dataset(dataset_id:str,payload:PreviewRequest,service:DatasetService=Depends(get_dataset_service)):return service.preview(dataset_id,payload.offset,payload.limit)
