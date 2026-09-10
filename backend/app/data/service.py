from __future__ import annotations
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from app.core.config import settings
from app.data.errors import DatasetError
from app.data.loader import load_dataframe, load_dataframe_path
from app.data.profile import profile_frame
from app.data.repository import DatasetRepository
from app.data.validator import analyze_target, validate_frame, validate_upload

class DatasetService:
    def __init__(self, repository: DatasetRepository | None=None, upload_dir: Path | None=None, max_size_mb: int | None=None) -> None:
        self.repository=repository or DatasetRepository()
        self.upload_dir=upload_dir or settings.upload_dir
        self.max_size_mb=max_size_mb or settings.max_upload_size_mb
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    def ingest(self, filename: str | None, content: bytes, content_type: str | None=None, target_column: str | None=None) -> dict:
        extension=validate_upload(filename,content,self.max_size_mb)
        digest=hashlib.sha256(content).hexdigest()
        existing=self.repository.find_by_hash(digest)
        if existing:
            summary=self._summary(existing)
            summary["warnings"]=[*summary["warnings"],"Identical dataset already registered; the existing record was reused."]
            return summary
        frame=load_dataframe(content,extension)
        warnings=validate_frame(frame)
        profile=profile_frame(frame)
        target=analyze_target(frame,target_column) if target_column else None
        if target: warnings.extend(target.pop("warnings"))
        dataset_id=str(uuid.uuid4())
        stored_filename=f"{dataset_id}{extension}"
        (self.upload_dir/stored_filename).write_bytes(content)
        record={"id":dataset_id,"name":Path(filename or "dataset").stem,"original_filename":Path(filename or "dataset").name,"stored_filename":stored_filename,"content_type":content_type,"extension":extension,"size_bytes":len(content),"sha256":digest,"profile":profile,"target_column":target_column,"target":target,"warnings":warnings,"created_at":datetime.now(timezone.utc).isoformat()}
        try:self.repository.create(record)
        except Exception:
            (self.upload_dir/stored_filename).unlink(missing_ok=True); raise
        return self._summary(record)
    def list(self) -> list[dict]: return [self._summary(record) for record in self.repository.list()]
    def get(self,dataset_id:str) -> dict:
        record=self.repository.get(dataset_id)
        if not record: raise DatasetError("DATASET_NOT_FOUND","Dataset was not found.",dataset_id,404)
        return self._summary(record)
    def select_target(self,dataset_id:str,target_column:str) -> dict:
        record=self.repository.get(dataset_id)
        if not record: raise DatasetError("DATASET_NOT_FOUND","Dataset was not found.",dataset_id,404)
        frame=load_dataframe_path(self.upload_dir/record["stored_filename"])
        target=analyze_target(frame,target_column); target_warnings=target.pop("warnings")
        warnings=[item for item in record["warnings"] if not item.startswith("Target is highly imbalanced")]+target_warnings
        self.repository.update_target(dataset_id,target_column,target,warnings)
        return self.get(dataset_id)
    def preview(self,dataset_id:str,offset:int=0,limit:int=20) -> dict:
        record=self.repository.get(dataset_id)
        if not record: raise DatasetError("DATASET_NOT_FOUND","Dataset was not found.",dataset_id,404)
        frame=load_dataframe_path(self.upload_dir/record["stored_filename"])
        page=frame.iloc[offset:offset+limit]
        rows=[{str(key):self._safe(value) for key,value in row.items()} for row in page.to_dict(orient="records")]
        return {"dataset_id":dataset_id,"columns":[str(column) for column in frame.columns],"rows":rows,"offset":offset,"limit":limit,"total_rows":len(frame)}
    @staticmethod
    def _safe(value: Any) -> Any:
        if pd.isna(value): return None
        if isinstance(value,np.generic): return value.item()
        if isinstance(value,(pd.Timestamp,datetime)): return value.isoformat()
        return value
    @staticmethod
    def _summary(record:dict) -> dict:
        result={key:record[key] for key in ("id","name","original_filename","extension","size_bytes","sha256","target_column","created_at")}
        result.update(record["profile"]); result["warnings"]=record.get("warnings",[])
        target=record.get("target") or {}
        result.update({"class_distribution":target.get("class_distribution"),"class_proportions":target.get("class_proportions"),"class_count":target.get("class_count"),"imbalance_ratio":target.get("imbalance_ratio")})
        return result
