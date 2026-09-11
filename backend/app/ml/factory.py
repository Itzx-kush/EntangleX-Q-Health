from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from app.ml.errors import ModelTrainingError
def build_estimator(config):
 weight=None if config.class_weight=="none" else "balanced"
 if config.model_type=="logistic_regression":return LogisticRegression(C=config.regularization_c,max_iter=config.max_iterations,class_weight=weight,random_state=config.random_seed,solver="liblinear")
 if config.model_type=="svm":return SVC(C=config.regularization_c,class_weight=weight,probability=True,random_state=config.random_seed)
 if config.model_type=="random_forest":return RandomForestClassifier(n_estimators=config.n_estimators,max_depth=config.max_depth,class_weight=weight,random_state=config.random_seed,n_jobs=-1)
 raise ModelTrainingError("UNSUPPORTED_MODEL","Unsupported classical model type.",config.model_type)
