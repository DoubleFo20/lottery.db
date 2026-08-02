import { Route, Routes } from 'react-router'
import { ROUTES } from '@/constants/routes'
import MainLayout from '@/layouts/MainLayout'
import HomePage from '@/pages/HomePage'
import DashboardPage from '@/pages/DashboardPage'
import LotteryHistoryPage from '@/pages/LotteryHistoryPage'
import PredictionPage from '@/pages/PredictionPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import SettingsPage from '@/pages/SettingsPage'
import NotFoundPage from '@/pages/NotFoundPage'

function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path={ROUTES.home} element={<HomePage />} />
        <Route path={ROUTES.dashboard} element={<DashboardPage />} />
        <Route path={ROUTES.history} element={<LotteryHistoryPage />} />
        <Route path={ROUTES.prediction} element={<PredictionPage />} />
        <Route path={ROUTES.analytics} element={<AnalyticsPage />} />
        <Route path={ROUTES.settings} element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

export default AppRoutes
