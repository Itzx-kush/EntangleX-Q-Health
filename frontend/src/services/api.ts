import {resolveApiBaseUrl} from './apiBase';
import type {HealthStatus} from '../types/health';
import type {DatasetPreview,DatasetSummary} from '../types/dataset';
import type {PreprocessingConfig,PreprocessingRun} from '../types/preprocessing';
import type {ModelRun,ModelTrainingConfig} from '../types/model';
import type {EvaluationRun} from '../types/evaluation';
import type {QuantumDiagnosticConfig,QuantumDiagnosticRun,QuantumRuntimeStatus} from '../types/quantum';
import type {EncodingConfig,EncodingRun,VQCConfig,VQCRun,QSVMConfig,QNNConfig,QuantumModelRun} from '../types/qml';
import type {BiomedicalValidationRequest,BiomedicalValidationResult,TrainingJob,TrainingJobConfig,TrainingJobList} from '../types/orchestration';
import type {Experiment,ExperimentComparison,ExperimentCreateRequest,ExperimentFilters,ExperimentList} from '../types/experiment';
import type {BenchmarkCreateRequest,BenchmarkList,BenchmarkReport} from '../types/benchmark';
import type {ClassicalExplainabilityRequest,ExplainabilityReport,QuantumExplainabilityRequest} from '../types/explainability';

const apiGlobal=globalThis as typeof globalThis&{ENTANGLEX_API_URL?:string};
const resolvedBase=resolveApiBaseUrl();
if(!apiGlobal.ENTANGLEX_API_URL)apiGlobal.ENTANGLEX_API_URL=resolvedBase;
const API_URL=apiGlobal.ENTANGLEX_API_URL??resolvedBase;
void import('../enhancements');

type ApiErrorBody={error?:string;message?:string;detail?:string;details?:string|null};
export class ApiRequestError extends Error{
  constructor(message:string,readonly kind:'timeout'|'network'|'http'|'invalid_response',readonly status:number|null=null,readonly code:string|null=null,readonly details:string|null=null){super(message);this.name='ApiRequestError'}
}
function isErrorBody(value:unknown):value is ApiErrorBody{return typeof value==='object'&&value!==null}
async function parse<T>(response:Response):Promise<T>{
  const raw=await response.text();let body:unknown=null;
  if(raw){try{body=JSON.parse(raw)}catch{throw new ApiRequestError(`The API returned invalid JSON (HTTP ${response.status}).`,'invalid_response',response.status)}}
  if(!response.ok){const error=isErrorBody(body)?body:{};throw new ApiRequestError(error.message??error.detail??`Request failed with HTTP ${response.status}.`,'http',response.status,error.error??null,error.details??null)}
  if(body===null)throw new ApiRequestError('The API returned an empty response.','invalid_response',response.status);
  return body as T;
}
async function fetchApi<T>(path:string,init?:RequestInit):Promise<T>{
  try{return await parse<T>(await fetch(`${API_URL}${path}`,init))}
  catch(error){if(error instanceof ApiRequestError)throw error;if(error instanceof DOMException&&error.name==='AbortError')throw error;throw new ApiRequestError(`The backend API at ${API_URL} could not be reached. Start FastAPI and verify the frontend host and port.`,'network',null,null,error instanceof Error?error.message:null)}
}
function post<T>(path:string,body:unknown){return fetchApi<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}

export const getHealth=()=>fetchApi<HealthStatus>('/health');
export async function uploadDataset(file:File):Promise<DatasetSummary>{
  const controller=new AbortController();const timer=globalThis.setTimeout(()=>controller.abort(),120_000);
  try{const form=new FormData();form.append('file',file);return await fetchApi<DatasetSummary>('/api/datasets/upload',{method:'POST',body:form,signal:controller.signal})}
  catch(error){if(error instanceof DOMException&&error.name==='AbortError')throw new ApiRequestError('Dataset registration timed out after 120 seconds. The backend may still be processing the file; check backend logs and health before retrying.','timeout');throw error}
  finally{globalThis.clearTimeout(timer)}
}
export const selectTarget=(id:string,target_column:string,task_type:'classification'|'regression'='classification')=>post<DatasetSummary>(`/api/datasets/${id}/target`,{target_column,task_type});
export const previewDataset=(id:string)=>post<DatasetPreview>(`/api/datasets/${id}/preview`,{offset:0,limit:10});
export const runPreprocessing=(config:PreprocessingConfig)=>post<PreprocessingRun>('/api/preprocessing/run',config);
export const trainModel=(config:ModelTrainingConfig)=>post<ModelRun>('/api/models/train',config);
export const listModelRuns=(preprocessingRunId?:string)=>fetchApi<{items:ModelRun[];total:number}>(`/api/models/runs${preprocessingRunId?`?preprocessing_run_id=${encodeURIComponent(preprocessingRunId)}`:''}`);
export const evaluateModel=(id:string)=>post<EvaluationRun>('/api/evaluations/run',{model_run_id:id});
export const listEvaluationRuns=(modelRunId?:string)=>fetchApi<{items:EvaluationRun[];total:number}>(`/api/evaluations/runs${modelRunId?`?model_run_id=${encodeURIComponent(modelRunId)}`:''}`);
export const getQuantumStatus=()=>fetchApi<QuantumRuntimeStatus>('/api/quantum/runtime/status');
export const runQuantumDiagnostic=(config:QuantumDiagnosticConfig)=>post<QuantumDiagnosticRun>('/api/quantum/runtime/diagnostics',config);
export const createEncoding=(config:EncodingConfig)=>post<EncodingRun>('/api/quantum/qml/encodings',config);
export const trainVQC=(config:VQCConfig)=>post<VQCRun>('/api/quantum/qml/vqc/train',config);
export const listVQCRuns=()=>fetchApi<{items:VQCRun[];total:number}>('/api/quantum/qml/vqc/runs');
export const trainQSVM=(config:QSVMConfig)=>post<QuantumModelRun>('/api/quantum/qml/qsvm/train',config);
export const trainQNN=(config:QNNConfig)=>post<QuantumModelRun>('/api/quantum/qml/qnn/train',config);
export const listQuantumModels=()=>fetchApi<{items:QuantumModelRun[];total:number}>('/api/quantum/qml/models');
export const getOrchestrationCapabilities=()=>fetchApi<{modalities:{modality:string;label:string;representation:string}[];models:string[]}>('/api/orchestration/capabilities');
export const validateBiomedical=(config:BiomedicalValidationRequest)=>post<BiomedicalValidationResult>('/api/orchestration/validate',config);
export const createTrainingJob=(config:TrainingJobConfig)=>post<TrainingJob>('/api/orchestration/jobs',config);
export const getTrainingJob=(id:string)=>fetchApi<TrainingJob>(`/api/orchestration/jobs/${id}`);
export const listTrainingJobs=(datasetId?:string)=>fetchApi<TrainingJobList>(`/api/orchestration/jobs${datasetId?`?dataset_id=${encodeURIComponent(datasetId)}`:''}`);
export const runTrainingJob=(id:string)=>post<TrainingJob>(`/api/orchestration/jobs/${id}/run`,{});
export const cancelTrainingJob=(id:string)=>post<TrainingJob>(`/api/orchestration/jobs/${id}/cancel`,{});
export const rerunTrainingJob=(id:string)=>post<TrainingJob>(`/api/orchestration/jobs/${id}/rerun`,{});
export const registerExperiment=(config:ExperimentCreateRequest)=>post<Experiment>('/api/experiments',config);
export const listExperiments=(filters:ExperimentFilters={})=>{const params=new URLSearchParams();for(const[key,value]of Object.entries(filters))if(value)params.set(key,value);return fetchApi<ExperimentList>(`/api/experiments${params.size?`?${params}`:''}`)};
export const getExperiment=(id:string)=>fetchApi<Experiment>(`/api/experiments/${id}`);
export const cloneExperiment=(id:string,parameter_overrides:Record<string,unknown>={})=>post<Experiment>(`/api/experiments/${id}/clone`,{parameter_overrides});
export async function deleteExperiment(id:string):Promise<void>{await fetchApi<unknown>(`/api/experiments/${id}`,{method:'DELETE'})}
export const compareExperiments=(experiment_ids:string[])=>post<ExperimentComparison>('/api/experiments/compare',{experiment_ids});
export const getExperimentCard=(id:string,kind:'dataset'|'model')=>fetchApi<Record<string,unknown>>(`/api/experiments/${id}/${kind}-card`);
export async function exportExperimentFile(id:string,format:'json'|'zip'){const response=await fetch(`${API_URL}/api/experiments/${id}/export?format=${format}`);if(!response.ok)throw new ApiRequestError(`Export failed with HTTP ${response.status}.`,'http',response.status);return response.blob()}
export const createBenchmark=(config:BenchmarkCreateRequest)=>post<BenchmarkReport>('/api/benchmarks',config);
export const listBenchmarks=()=>fetchApi<BenchmarkList>('/api/benchmarks');
export const getBenchmark=(id:string)=>fetchApi<BenchmarkReport>(`/api/benchmarks/${id}`);
export const createClassicalExplanation=(config:ClassicalExplainabilityRequest)=>post<ExplainabilityReport>('/api/explainability/classical',config);
export const createQuantumExplanation=(config:QuantumExplainabilityRequest)=>post<ExplainabilityReport>('/api/explainability/quantum',config);
export const listExplainabilityReports=(phase?:string)=>fetchApi<{items:ExplainabilityReport[];total:number}>(`/api/explainability/reports${phase?`?phase=${encodeURIComponent(phase)}`:''}`);
export type PredictionRequest={model_run_id:string;features?:number[];sample_index?:number;probability_threshold?:number;low_risk_max?:number;intermediate_risk_max?:number};
export type PredictionRecord={id:string;model_run_id:string;model_type:string;task_type:string;input_source:string;sample_index:number|null;feature_count:number;prediction:unknown;probability:number|null;threshold:number|null;risk_band:string;decision:string;uncertainty_status:string;scientific_warnings:string[];created_at:string};
export const createPrediction=(config:PredictionRequest)=>post<PredictionRecord>('/api/predictions',config);
export const listPredictions=(modelRunId?:string)=>fetchApi<{items:PredictionRecord[];total:number}>(`/api/predictions${modelRunId?`?model_run_id=${encodeURIComponent(modelRunId)}`:''}`);
