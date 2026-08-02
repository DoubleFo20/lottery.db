import { Link } from 'react-router'
import { ROUTES } from '@/constants/routes'
import { useHealth } from '@/hooks/useHealth'
import { useToast } from '@/hooks/useToast'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import ErrorMessage from '@/components/common/ErrorMessage'
import PageContainer from '@/components/common/PageContainer'
import { getHttpErrorMessage } from '@/utils/httpError'

function HomePage() {
  const { data, isPending, isError, error, refetch, isRefetching } = useHealth()
  const { showToast } = useToast()

  return (
    <PageContainer title="Home" description="Lottery foundation application">
      <Card title="Backend status">
        {isPending && <LoadingSpinner label="Connecting to backend..." />}
        {isError && (
          <ErrorMessage
            title="Backend unavailable"
            message={getHttpErrorMessage(error)}
            onRetry={() => void refetch()}
          />
        )}
        {data && (
          <div className="health-status">
            <span className="health-status__badge">Backend Connected</span>
            <p>Status: {data.status}</p>
          </div>
        )}
        {isRefetching && <p className="muted">Retrying...</p>}
      </Card>
      <Card title="Welcome">
        <p>Use the navigation to explore the application.</p>
        <div className="row">
          <Link to={ROUTES.dashboard}>
            <Button type="button" variant="secondary">
              Go to Dashboard
            </Button>
          </Link>
          <Button type="button" onClick={() => showToast('Hello from Lottery!', 'success')}>
            Show toast
          </Button>
        </div>
      </Card>
    </PageContainer>
  )
}

export default HomePage
