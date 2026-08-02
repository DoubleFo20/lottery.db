import PageContainer from '@/components/common/PageContainer'
import EmptyState from '@/components/common/EmptyState'
import Card from '@/components/ui/Card'

function DashboardPage() {
  return (
    <PageContainer title="Dashboard" description="Overview of lottery activity and trends">
      <Card>
        <EmptyState title="Dashboard" message="Dashboard content coming soon." />
      </Card>
    </PageContainer>
  )
}

export default DashboardPage
