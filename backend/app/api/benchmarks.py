from __future__ import annotations

from fastapi import APIRouter, Depends

from app.benchmarking.schemas import BenchmarkCreateRequest, BenchmarkListResponse
from app.benchmarking.service import BenchmarkService


router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])
_service: BenchmarkService | None = None


def get_service() -> BenchmarkService:
    global _service
    if _service is None:
        _service = BenchmarkService()
    return _service


@router.post("", status_code=201)
def create_benchmark(payload: BenchmarkCreateRequest, service: BenchmarkService = Depends(get_service)):
    return service.create(payload)


@router.get("", response_model=BenchmarkListResponse)
def list_benchmarks(service: BenchmarkService = Depends(get_service)):
    items = service.list()
    return {"items": items, "total": len(items)}


@router.get("/{benchmark_id}")
def get_benchmark(benchmark_id: str, service: BenchmarkService = Depends(get_service)):
    return service.get(benchmark_id)
