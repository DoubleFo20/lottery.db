import { useQuery } from '@tanstack/react-query'
import { getHealth, type HealthResponse } from '@/services/health'

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: getHealth,
    retry: 2,
    staleTime: 30_000,
  })
}
