import { useEffect, useState } from 'react'
import { Outlet } from 'react-router'
import TopNavigation from '@/components/TopNavigation'
import Sidebar from '@/components/Sidebar'
import Footer from '@/components/Footer'

function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setSidebarOpen(false)
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div className="app-shell">
      <TopNavigation onMenuToggle={() => setSidebarOpen((open) => !open)} />
      <div className="app-body">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="app-main">
          <div className="app-main__inner">
            <Outlet />
          </div>
        </main>
      </div>
      <Footer />
    </div>
  )
}

export default MainLayout
