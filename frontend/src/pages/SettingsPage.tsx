import PageContainer from '@/components/common/PageContainer'
import EmptyState from '@/components/common/EmptyState'
import Card from '@/components/ui/Card'

function SettingsPage() {
  return (
    <PageContainer title="Settings" description="Application preferences">
      <Card>
        <EmptyState title="Settings" message="Settings content coming soon." />
      </Card>
    </PageContainer>
  )
}

export default SettingsPage
