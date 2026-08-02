import { Link } from 'react-router'
import { ROUTES } from '@/constants/routes'
import PageContainer from '@/components/common/PageContainer'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

function NotFoundPage() {
  return (
    <PageContainer title="404 — Page not found">
      <Card>
        <p>The page you are looking for does not exist.</p>
        <Link to={ROUTES.home}>
          <Button type="button" variant="secondary">
            Go back home
          </Button>
        </Link>
      </Card>
    </PageContainer>
  )
}

export default NotFoundPage
