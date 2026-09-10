import type {HealthStatus} from "../types/health";
import type {DatasetPreview,DatasetSummary} from "../types/dataset";
const API_URL=(globalThis as any).ENTANGLEX_API_URL ?? "http://localhost:8000";
async function parse<T>(response:Response):Promise<T>{const body=await response.json();if(!response.ok)throw new Error(body.message??`Request failed: ${response.status}`);return body as T}
export async function getHealth():Promise<HealthStatus>{return parse(await fetch(`${API_URL}/health`))}
export async function uploadDataset(file:File):Promise<DatasetSummary>{const data=new FormData();data.append("file",file);return parse(await fetch(`${API_URL}/api/datasets/upload`,{method:"POST",body:data}))}
export async function selectTarget(datasetId:string,targetColumn:string):Promise<DatasetSummary>{return parse(await fetch(`${API_URL}/api/datasets/${datasetId}/target`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target_column:targetColumn})}))}
export async function previewDataset(datasetId:string):Promise<DatasetPreview>{return parse(await fetch(`${API_URL}/api/datasets/${datasetId}/preview`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({offset:0,limit:10})}))}
