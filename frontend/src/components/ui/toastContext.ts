import { createContext } from 'react'
import type { ToastVariant } from '@/types'

export interface ToastContextValue {
  showToast: (message: string, variant?: ToastVariant) => void
  dismissToast: (id: number) => void
}

export const ToastContext = createContext<ToastContextValue | null>(null)
