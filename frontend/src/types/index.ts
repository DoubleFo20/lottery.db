export interface ApiResponse<T> {
  success: boolean
  message: string
  data: T | null
}

export type Theme = 'light' | 'dark'

export type ToastVariant = 'success' | 'error' | 'info'
