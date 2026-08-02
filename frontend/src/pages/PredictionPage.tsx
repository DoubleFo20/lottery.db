import PageContainer from '@/components/common/PageContainer'
import EmptyState from '@/components/common/EmptyState'
import Card from '@/components/ui/Card'

function PredictionPage() {
  return (
    <PageContainer title="Prediction" description="Predicted numbers">
      <Card>
        <EmptyState title="Prediction" message="Prediction content coming soon." />
      </Card>
    </PageContainer>
  )
}

export default PredictionPage
