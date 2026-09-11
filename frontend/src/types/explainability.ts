export type ExplainabilityReport={id:string;phase:string;target_type:string;run_id:string;payload:Record<string,any>;created_at:string};
export type ClassicalExplainabilityRequest={model_run_id:string;evaluation_run_id?:string|null;sample_limit?:number;top_k?:number;thresholds?:number[]};
export type QuantumExplainabilityRequest={model_type:'vqc'|'qsvm'|'qnn';run_ids:string[];sample_limit?:number;top_k?:number;feature_delta?:number;parameter_delta?:number};
