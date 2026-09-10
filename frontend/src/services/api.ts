import type {HealthStatus} from "../types/health";
const API_URL=(globalThis as any).ENTANGLEX_API_URL ?? "http://localhost:8000";
export async function getHealth():Promise<HealthStatus>{const response=await fetch(`${API_URL}/health`);if(!response.ok)throw new Error(`Health request failed: ${response.status}`);return response.json() as Promise<HealthStatus>}
