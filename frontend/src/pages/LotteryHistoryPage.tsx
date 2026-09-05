import { useState } from 'react'
import PageContainer from '@/components/common/PageContainer'
import EmptyState from '@/components/common/EmptyState'
import ErrorMessage from '@/components/common/ErrorMessage'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import { useHistory } from '@/hooks/useHistory'
import { formatDate } from '@/utils/format'
import { getHttpErrorMessage } from '@/utils/httpError'

const PAGE_SIZE = 20

function LotteryHistoryPage() {
  const [offset, setOffset] = useState(0)
  const { data, isPending, isError, error, refetch, isFetching } = useHistory(offset, PAGE_SIZE)
  const pageStart = data && data.total > 0 ? data.offset + 1 : 0
  const pageEnd = data ? Math.min(data.offset + data.items.length, data.total) : 0

  return (
    <PageContainer title="Lottery History" description="Past draw results">
      <Card title="Official draw history">
        {isPending && <LoadingSpinner label="Loading lottery history..." />}
        {isError && (
          <ErrorMessage
            title="Lottery history unavailable"
            message={getHttpErrorMessage(error)}
            onRetry={() => void refetch()}
          />
        )}
        {data?.total === 0 && (
          <EmptyState title="No draw results" message="No lottery history has been imported yet." />
        )}
        {data && data.total > 0 && (
          <>
            <div className="history-summary">
              <p>
                Showing {pageStart}-{pageEnd} of {data.total} draws
              </p>
              {isFetching && <span className="muted">Updating...</span>}
            </div>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th scope="col">Draw date</th>
                    <th scope="col">First prize</th>
                    <th scope="col">Last 2 digits</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((draw) => (
                    <tr key={draw.id}>
                      <td>{formatDate(`${draw.draw_date}T00:00:00`)}</td>
                      <td>
                        <span className="lottery-number lottery-number--primary">
                          {draw.first_prize}
                        </span>
                      </td>
                      <td>
                        <span className="lottery-number">{draw.last_two ?? '-'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination" aria-label="Lottery history pagination">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={offset === 0 || isFetching}
                onClick={() => setOffset((current) => Math.max(0, current - PAGE_SIZE))}
              >
                Previous
              </Button>
              <span className="muted">
                Page {Math.floor(offset / PAGE_SIZE) + 1} of {Math.ceil(data.total / PAGE_SIZE)}
              </span>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={offset + PAGE_SIZE >= data.total || isFetching}
                onClick={() => setOffset((current) => current + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </>
        )}
      </Card>
    </PageContainer>
  )
}

export default LotteryHistoryPage
