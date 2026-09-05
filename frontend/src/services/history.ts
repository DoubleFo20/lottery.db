import { client } from '@/api/client'
import type { ApiResponse } from '@/types'

export interface LotteryHistoryItem {
  id: number
  draw_date: string
  first_prize: string
  last_two: string | null
}

export interface LotteryHistoryPage {
  items: LotteryHistoryItem[]
  total: number
  offset: number
  limit: number
}

export async function getHistory(offset: number, limit: number): Promise<LotteryHistoryPage> {
  const { data: response } = await client.get<ApiResponse<LotteryHistoryPage>>('/history', {
    params: { offset, limit },
  })

  if (!response.success || !response.data) {
    throw new Error(response.message)
  }

  return response.data
}
