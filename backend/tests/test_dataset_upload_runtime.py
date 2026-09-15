from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from fastapi.testclient import TestClient
from app.api.datasets import get_dataset_service
from app.data.errors import DatasetError
from app.data.repository import DatasetRepository
from app.data.service import DatasetService
from app.main import create_app

def setup_client(root:Path):
    service=DatasetService(DatasetRepository(f"sqlite:///{root/'datasets.db'}"),root/'uploads',2)
    app=create_app();app.dependency_overrides[get_dataset_service]=lambda:service
    return TestClient(app),service

def test_small_csv_and_duplicate_upload_are_real_and_idempotent():
    with TemporaryDirectory() as directory:
        client,service=setup_client(Path(directory));content=b"age,marker,target\n31,2.1,0\n52,8.4,1\n"
        first=client.post('/api/datasets/upload',files={'file':('medical.csv',content,'text/csv')})
        second=client.post('/api/datasets/upload',files={'file':('medical.csv',content,'text/csv')})
        assert first.status_code==201 and second.status_code==201
        assert first.json()['id']==second.json()['id']
        assert first.json()['rows']==2 and len(first.json()['sha256'])==64
        assert len(service.list())==1

def test_small_xlsx_registration_returns_complete_summary():
    with TemporaryDirectory() as directory:
        client,_=setup_client(Path(directory));buffer=BytesIO();pd.DataFrame({'age':[20,65],'marker':[1.2,9.1],'target':[0,1]}).to_excel(buffer,index=False,engine='openpyxl')
        response=client.post('/api/datasets/upload',files={'file':('medical.xlsx',buffer.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
        assert response.status_code==201
        body=response.json();assert body['extension']=='.xlsx';assert body['rows']==2;assert body['columns']==3

def test_larger_realistic_biomedical_csv_profiles_without_changing_rows():
    with TemporaryDirectory() as directory:
        root=Path(directory);service=DatasetService(DatasetRepository(f"sqlite:///{root/'large.db'}"),root/'uploads',5)
        rows=['age,bmi,biomarker,group,target']+[f"{20+i%60},{18+(i%25)*.4:.1f},{(i%17)*.23:.2f},{'A' if i%2 else 'B'},{i%2}" for i in range(25000)]
        result=service.ingest('biomedical.csv',('\n'.join(rows)+'\n').encode())
        assert result['rows']==25000;assert result['columns']==5;assert result['numeric_columns']==['age','bmi','biomarker','target'];assert result['categorical_columns']==['group']

def test_invalid_empty_unsupported_malformed_and_oversized_uploads_are_explicit():
    with TemporaryDirectory() as directory:
        root=Path(directory);client,service=setup_client(root)
        cases=[('empty.csv',b'','EMPTY_FILE'),('notes.txt',b'a\n1\n','UNSUPPORTED_FILE_TYPE'),('broken.xlsx',b'not an xlsx','DATASET_PARSE_FAILED'),('broken.csv',b'"unclosed\n','DATASET_PARSE_FAILED')]
        for name,content,code in cases:
            response=client.post('/api/datasets/upload',files={'file':(name,content,'application/octet-stream')})
            assert response.status_code==400;assert response.json()['error']==code
        try:service.ingest('large.csv',b'a\n'+b'1\n'*(1024*1024+1))
        except DatasetError as error:assert error.code=='FILE_TOO_LARGE' and error.status_code==413
        else:raise AssertionError('oversized upload was accepted')

def test_target_selection_remains_available_after_registration():
    with TemporaryDirectory() as directory:
        client,_=setup_client(Path(directory));content=b"age,target\n20,0\n40,1\n"
        dataset=client.post('/api/datasets/upload',files={'file':('target.csv',content,'text/csv')}).json()
        response=client.post(f"/api/datasets/{dataset['id']}/target",json={'target_column':'target','task_type':'classification'})
        assert response.status_code==200;assert response.json()['target_column']=='target';assert response.json()['class_count']==2
