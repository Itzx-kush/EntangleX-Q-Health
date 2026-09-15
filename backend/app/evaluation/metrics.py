import numpy as np
from sklearn.metrics import accuracy_score,average_precision_score,balanced_accuracy_score,confusion_matrix,f1_score,precision_recall_curve,precision_score,recall_score,roc_auc_score,roc_curve

def _threshold(value):
 value=float(value)
 return value if np.isfinite(value) else None

def evaluate_binary(y_true,y_pred,scores=None):
 y_true=np.asarray(y_true);y_pred=np.asarray(y_pred);tn,fp,fn,tp=[int(x) for x in confusion_matrix(y_true,y_pred,labels=[0,1]).ravel()];specificity=tn/(tn+fp) if tn+fp else 0.0
 auc=None;pr_auc=None;roc_points=[];pr_points=[]
 if scores is not None and len(np.unique(y_true))==2:
  values=np.asarray(scores,dtype=float);auc=float(roc_auc_score(y_true,values));pr_auc=float(average_precision_score(y_true,values))
  fpr,tpr,rt=roc_curve(y_true,values);precision,recall,pt=precision_recall_curve(y_true,values)
  roc_points=[{'false_positive_rate':float(x),'true_positive_rate':float(y),'threshold':_threshold(t)} for x,y,t in zip(fpr,tpr,rt)]
  pr_points=[{'recall':float(x),'precision':float(y),'threshold':_threshold(pt[i]) if i<len(pt) else None} for i,(x,y) in enumerate(zip(recall,precision))]
 return {'accuracy':float(accuracy_score(y_true,y_pred)),'balanced_accuracy':float(balanced_accuracy_score(y_true,y_pred)),'precision':float(precision_score(y_true,y_pred,zero_division=0)),'recall':float(recall_score(y_true,y_pred,zero_division=0)),'f1':float(f1_score(y_true,y_pred,zero_division=0)),'sensitivity':float(recall_score(y_true,y_pred,zero_division=0)),'specificity':float(specificity),'roc_auc':auc,'pr_auc':pr_auc,'roc_curve':roc_points,'precision_recall_curve':pr_points,'true_negative':tn,'false_positive':fp,'false_negative':fn,'true_positive':tp,'support_negative':tn+fp,'support_positive':tp+fn}

def model_scores(model,X):
 if hasattr(model,'predict_proba'):return model.predict_proba(X)[:,1]
 if hasattr(model,'decision_function'):return model.decision_function(X)
 return None
