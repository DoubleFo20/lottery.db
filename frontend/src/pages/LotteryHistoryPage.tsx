import PageContainer from '@/components/common/PageContainer'
import EmptyState from '@/components/common/EmptyState'
import Card from '@/components/ui/Card'

function LotteryHistoryPage() {
  return (
    <PageContainer title="Lottery History" description="Past draw results">
      <Card>
        <EmptyState title="Lottery History" message="Lottery history content coming soon." />
      </Card>
    </PageContainer>
  )
}

export default LotteryHistoryPage
