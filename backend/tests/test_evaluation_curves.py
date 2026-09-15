import numpy as np
from app.evaluation.metrics import evaluate_binary

def test_binary_evaluation_returns_measured_roc_and_pr_curves():
    y=np.asarray([0,0,1,1]);scores=np.asarray([.1,.4,.35,.8]);pred=(scores>=.5).astype(int)
    result=evaluate_binary(y,pred,scores)
    assert result['roc_auc']==.75
    assert result['pr_auc'] is not None
    assert len(result['roc_curve'])>=2
    assert len(result['precision_recall_curve'])>=2
    assert all(0<=point['false_positive_rate']<=1 and 0<=point['true_positive_rate']<=1 for point in result['roc_curve'])
    assert all(0<=point['recall']<=1 and 0<=point['precision']<=1 for point in result['precision_recall_curve'])
    assert result['roc_curve'][0]['threshold'] is None

def test_curves_remain_empty_when_scores_are_unavailable():
    result=evaluate_binary([0,1],[0,1],None)
    assert result['roc_auc'] is None and result['pr_auc'] is None
    assert result['roc_curve']==[] and result['precision_recall_curve']==[]
