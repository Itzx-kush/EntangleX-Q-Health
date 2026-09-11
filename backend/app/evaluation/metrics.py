import numpy as np
from sklearn.metrics import accuracy_score,balanced_accuracy_score,confusion_matrix,f1_score,precision_score,recall_score,roc_auc_score
def evaluate_binary(y_true,y_pred,scores=None):
 y_true=np.asarray(y_true);y_pred=np.asarray(y_pred);tn,fp,fn,tp=[int(x) for x in confusion_matrix(y_true,y_pred,labels=[0,1]).ravel()];specificity=tn/(tn+fp) if tn+fp else 0.0
 auc=None
 if scores is not None and len(np.unique(y_true))==2:auc=float(roc_auc_score(y_true,np.asarray(scores)))
 return {'accuracy':float(accuracy_score(y_true,y_pred)),'balanced_accuracy':float(balanced_accuracy_score(y_true,y_pred)),'precision':float(precision_score(y_true,y_pred,zero_division=0)),'recall':float(recall_score(y_true,y_pred,zero_division=0)),'f1':float(f1_score(y_true,y_pred,zero_division=0)),'sensitivity':float(recall_score(y_true,y_pred,zero_division=0)),'specificity':float(specificity),'roc_auc':auc,'true_negative':tn,'false_positive':fp,'false_negative':fn,'true_positive':tp,'support_negative':tn+fp,'support_positive':tp+fn}
def model_scores(model,X):
 if hasattr(model,'predict_proba'):return model.predict_proba(X)[:,1]
 if hasattr(model,'decision_function'):return model.decision_function(X)
 return None
