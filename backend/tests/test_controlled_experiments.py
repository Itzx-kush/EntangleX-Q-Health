from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from app.controlled_experiments.repository import ControlledExperimentRepository
from app.controlled_experiments.schemas import ControlledExperimentRequest

def test_model_selection_is_explicit_and_unique():
    request=ControlledExperimentRequest(name='comparison',preprocessing_run_id='prep-1',models=['logistic_regression','vqc'])
    assert request.models==['logistic_regression','vqc']
    with pytest.raises(ValueError):ControlledExperimentRequest(name='bad',preprocessing_run_id='prep-1',models=['vqc','vqc'])

def test_repository_preserves_independent_model_outcomes_and_fingerprint():
    with TemporaryDirectory() as directory:
        repo=ControlledExperimentRepository(f"sqlite:///{Path(directory)/'controlled.db'}")
        repo.create_experiment({'id':'e1','name':'one experiment','preprocessing_run_id':'p1','encoding_run_id':'q1','comparison_fingerprint':'a'*64,'status':'running','configuration':{'shared_conditions':{'split_seed':42}},'warnings':['research only'],'parent_experiment_id':None,'created_at':'2026-01-01T00:00:00+00:00'})
        for identifier,model in [('j1','logistic_regression'),('j2','vqc')]:repo.create_job({'id':identifier,'experiment_id':'e1','model_type':model,'status':'queued','stage':'queued','checkpoint':0,'total_checkpoints':3,'created_at':'2026-01-01T00:00:00+00:00'})
        repo.update_job('j1',status='succeeded',stage='completed',result_json={'metrics':{'f1':.8}})
        repo.update_job('j2',status='failed',stage='failed',error_json={'code':'QISKIT_UNAVAILABLE','message':'not installed'})
        jobs=repo.jobs('e1'); assert jobs[0]['result']['metrics']['f1']==.8; assert jobs[1]['error']['code']=='QISKIT_UNAVAILABLE'; assert repo.get_experiment('e1')['comparison_fingerprint']=='a'*64
