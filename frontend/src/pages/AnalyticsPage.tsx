import PageContainer from '@/components/common/PageContainer'
import EmptyState from '@/components/common/EmptyState'
import Card from '@/components/ui/Card'

function AnalyticsPage() {
  return (
    <PageContainer title="Analytics" description="Statistical analysis and insights">
      <Card>
        <EmptyState title="Analytics" message="Analytics content coming soon." />
      </Card>
    </PageContainer>
  )
}

export default AnalyticsPage
