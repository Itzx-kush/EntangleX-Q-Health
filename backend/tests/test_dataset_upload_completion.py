from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from app.api.datasets import get_dataset_service
from app.data.repository import DatasetRepository
from app.data.service import DatasetService
from app.main import create_app

def test_upload_returns_201_summary_and_duplicate_is_idempotent():
 with TemporaryDirectory() as directory:
  root=Path(directory);service=DatasetService(DatasetRepository(f"sqlite:///{root/'data.db'}"),root/'uploads',1);app=create_app();app.dependency_overrides[get_dataset_service]=lambda:service;client=TestClient(app);content=b'age,marker,target\n20,1.2,0\n60,8.4,1\n'
  first=client.post('/api/datasets/upload',files={'file':('medical.csv',content,'text/csv')});second=client.post('/api/datasets/upload',files={'file':('medical.csv',content,'text/csv')})
  assert first.status_code==201 and second.status_code==201;assert first.json()['id']==second.json()['id'];assert first.json()['rows']==2;assert len(first.json()['sha256'])==64;assert len(service.list())==1

def test_upload_errors_terminate_with_structured_responses():
 with TemporaryDirectory() as directory:
  root=Path(directory);service=DatasetService(DatasetRepository(f"sqlite:///{root/'data.db'}"),root/'uploads',1);app=create_app();app.dependency_overrides[get_dataset_service]=lambda:service;client=TestClient(app)
  for name,content,code in [('empty.csv',b'','EMPTY_FILE'),('bad.txt',b'a\n1\n','UNSUPPORTED_FILE_TYPE'),('broken.xlsx',b'bad workbook','DATASET_PARSE_FAILED')]:
   response=client.post('/api/datasets/upload',files={'file':(name,content,'application/octet-stream')});assert response.status_code==400;assert response.json()['error']==code
