import { client } from '@/api/client'

export interface HealthResponse {
  status: string
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await client.get<HealthResponse>('/health')
  return data
}
