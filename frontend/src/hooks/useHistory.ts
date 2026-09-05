import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { getHistory, type LotteryHistoryPage } from '@/services/history'

export function useHistory(offset: number, limit: number) {
  return useQuery<LotteryHistoryPage>({
    queryKey: ['history', offset, limit],
    queryFn: () => getHistory(offset, limit),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  })
}
