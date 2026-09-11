export type BiomedicalModality='ehr'|'genomics'|'medical_image';
export type TrainingModelType='logistic_regression'|'svm'|'random_forest'|'vqc'|'qsvm'|'qnn';
export type TrainingStatus='queued'|'running'|'completed'|'failed'|'cancel_requested'|'cancelled';
export type BiomedicalValidationRequest={modality:BiomedicalModality;samples:number;columns?:{name:string;kind?:'numeric'|'categorical'|'datetime'|'text'}[];features?:number;feature_names?:string[];numeric?:boolean;target_column?:string;representation?:'embedding'|'engineered_features';embedding_dim?:number};
export type BiomedicalValidationResult={modality:BiomedicalModality;valid:boolean;normalized:Record<string,unknown>;warnings:string[]};
export type TrainingJobConfig={model_type:TrainingModelType;modality:BiomedicalModality;dataset_id?:string;preprocessing_run_id?:string;encoding_run_id?:string;model_parameters?:Record<string,unknown>;seed?:number;parent_job_id?:string};
export type TrainingJob={id:string;model_type:TrainingModelType;modality:BiomedicalModality;dataset_id:string|null;preprocessing_run_id:string|null;encoding_run_id:string|null;status:TrainingStatus;progress:number;configuration:Record<string,unknown>;result:Record<string,unknown>|null;error:Record<string,unknown>|null;cancel_requested:boolean;parent_job_id:string|null;created_at:string;started_at:string|null;finished_at:string|null};
export type TrainingJobList={items:TrainingJob[];total:number};
