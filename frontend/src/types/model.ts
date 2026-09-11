export type ModelType="logistic_regression"|"svm"|"random_forest";
export type ModelTrainingConfig={preprocessing_run_id:string;model_type:ModelType;random_seed:number;regularization_c:number;max_iterations:number;n_estimators:number;max_depth:number|null;class_weight:"none"|"balanced"};
export type ModelRun={id:string;preprocessing_run_id:string;dataset_id:string;status:string;model_type:ModelType;configuration:ModelTrainingConfig;training_rows:number;feature_count:number;class_distribution:Record<string,number>;training_duration_seconds:number;artifact_path:string;created_at:string};
