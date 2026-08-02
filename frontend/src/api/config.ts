import type { AxiosRequestConfig } from 'axios'
import { env } from '@/config/env'

export const apiConfig: AxiosRequestConfig = {
  baseURL: env.apiBaseUrl,
  timeout: env.requestTimeoutMs,
  headers: {
    'Content-Type': 'application/json',
  },
}
