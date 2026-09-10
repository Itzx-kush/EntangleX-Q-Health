from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
def build_estimator(c):
 w=None if c.class_weight=='none' else 'balanced'
 if c.model_type=='logistic_regression':return LogisticRegression(C=c.regularization_c,max_iter=c.max_iterations,class_weight=w,random_state=c.random_seed,solver='liblinear')
 if c.model_type=='svm':return SVC(C=c.regularization_c,class_weight=w,probability=True,random_state=c.random_seed)
 return RandomForestClassifier(n_estimators=c.n_estimators,max_depth=c.max_depth,class_weight=w,random_state=c.random_seed,n_jobs=-1)
