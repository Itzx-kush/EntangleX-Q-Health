from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from app.main import create_app
from app.api.qml import qnn_service, qsvm_service, vqc_service
from app.quantum.qml_repository import QMLRepository
from app.quantum.qnn import QNNService
from app.quantum.qsvm import QSVMService
from app.quantum.vqc import VQCService

METRICS={"accuracy":.7,"balanced_accuracy":.69,"precision":.68,"recall":.67,"f1":.675,"sensitivity":.67,"specificity":.71,"roc_auc":.72,"true_negative":7,"false_positive":3,"false_negative":2,"true_positive":8}

def vqc_record(identifier="v1",encoding="enc-1",created="2026-01-01T00:00:01+00:00",status="completed"):
    return {"id":identifier,"encoding_run_id":encoding,"preprocessing_run_id":"prep-1","dataset_id":"data-1","status":status,"configuration":{"encoding_run_id":encoding,"ansatz_reps":1,"optimizer":"cobyla","max_iterations":2,"tolerance":.001,"training_samples":4,"evaluation_samples":4,"seed":42},"summary":{"training_rows":4,"evaluation_rows":4,"parameter_count":2,"iterations_completed":2,"initial_loss":.8,"final_loss":.7,"best_loss":.7,"converged":False,"termination_reason":"optimizer_stopped_without_convergence","optimizer_message":"bounded test record","training_duration_seconds":.01,**METRICS,"circuit_depth":3,"circuit_size":4,"operation_counts":{"ry":2,"cx":1},"loss_history":[.8,.7]},"artifact_path":f"vqc/{identifier}.npz","created_at":created}

def model_record(model_type,identifier,encoding="enc-1",created="2026-01-01T00:00:02+00:00",status="completed"):
    task="classification"
    return {"id":identifier,"model_type":model_type,"task_type":task,"encoding_run_id":encoding,"preprocessing_run_id":"prep-1","dataset_id":"data-1","status":status,"configuration":{"encoding_run_id":encoding,"task_type":task,"training_samples":4,"evaluation_samples":4,"seed":42},"summary":{"training_rows":4,"evaluation_rows":4,"parameter_count":0 if model_type=="qsvm" else 5,"training_duration_seconds":.01,"circuit_depth":3,"circuit_size":4,"operation_counts":{"ry":2,"cx":1},"metrics":METRICS,"training_history":[],"converged":True,"optimizer_message":"completed"},"artifact_path":f"{model_type}/{identifier}.joblib","created_at":created}

def client_for(repo:QMLRepository,root:Path):
    app=create_app()
    app.dependency_overrides[vqc_service]=lambda:VQCService(runs=repo,artifact_dir=root/"vqc")
    app.dependency_overrides[qsvm_service]=lambda:QSVMService(runs=repo,artifact_dir=root/"qsvm")
    app.dependency_overrides[qnn_service]=lambda:QNNService(runs=repo,artifact_dir=root/"qnn")
    return TestClient(app,raise_server_exceptions=False)

def test_empty_registry_returns_success():
    with TemporaryDirectory() as directory:
        root=Path(directory); repo=QMLRepository(f"sqlite:///{root/'qml.db'}")
        response=client_for(repo,root).get("/api/quantum/qml/models")
        assert response.status_code==200
        assert response.json()=={"items":[],"total":0}

def test_each_model_family_is_explicitly_serialized():
    cases=[("vqc","v1"),("qsvm","s1"),("qnn","n1")]
    for family,identifier in cases:
        with TemporaryDirectory() as directory:
            root=Path(directory); repo=QMLRepository(f"sqlite:///{root/'qml.db'}")
            repo.create_vqc(vqc_record(identifier)) if family=="vqc" else repo.create_model(model_record(family,identifier))
            response=client_for(repo,root).get("/api/quantum/qml/models")
            assert response.status_code==200
            payload=response.json(); assert payload["total"]==1; assert payload["items"][0]["model_type"]==family; assert payload["items"][0]["status"]=="completed"; assert "metrics" in payload["items"][0]

def test_combined_registry_is_sorted_and_filterable_without_duplication():
    with TemporaryDirectory() as directory:
        root=Path(directory); repo=QMLRepository(f"sqlite:///{root/'qml.db'}")
        repo.create_vqc(vqc_record("v1","enc-1","2026-01-01T00:00:01+00:00",status="running"))
        repo.create_model(model_record("qsvm","s1","enc-1","2026-01-01T00:00:03+00:00"))
        repo.create_model(model_record("qnn","n1","enc-1","2026-01-01T00:00:02+00:00"))
        repo.create_vqc(vqc_record("v2","enc-2","2026-01-01T00:00:04+00:00"))
        client=client_for(repo,root)
        payload=client.get("/api/quantum/qml/models",params={"encoding_run_id":"enc-1"}).json()
        assert payload["total"]==3
        assert [item["model_type"] for item in payload["items"]]==["qsvm","qnn","vqc"]
        assert {item["encoding_run_id"] for item in payload["items"]}=={"enc-1"}
        assert next(item for item in payload["items"] if item["model_type"]=="vqc")["status"]=="running"

def test_unknown_persisted_model_type_fails_explicitly():
    with TemporaryDirectory() as directory:
        root=Path(directory); repo=QMLRepository(f"sqlite:///{root/'qml.db'}")
        repo.create_model(model_record("unsupported","x1"))
        response=client_for(repo,root).get("/api/quantum/qml/models")
        assert response.status_code==500
        assert response.json()["error"]=="UNSUPPORTED_QUANTUM_MODEL_TYPE"

def test_existing_family_get_endpoints_keep_their_contracts():
    with TemporaryDirectory() as directory:
        root=Path(directory); repo=QMLRepository(f"sqlite:///{root/'qml.db'}")
        repo.create_vqc(vqc_record()); repo.create_model(model_record("qsvm","s1")); repo.create_model(model_record("qnn","n1"))
        client=client_for(repo,root)
        assert client.get("/api/quantum/qml/vqc/v1").json()["id"]=="v1"
        assert client.get("/api/quantum/qml/qsvm/s1").json()["model_type"]=="qsvm"
        assert client.get("/api/quantum/qml/qnn/n1").json()["model_type"]=="qnn"
