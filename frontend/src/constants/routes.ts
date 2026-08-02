export const ROUTES = {
  home: '/',
  dashboard: '/dashboard',
  history: '/history',
  prediction: '/prediction',
  analytics: '/analytics',
  settings: '/settings',
} as const

export type RoutePath = (typeof ROUTES)[keyof typeof ROUTES]
