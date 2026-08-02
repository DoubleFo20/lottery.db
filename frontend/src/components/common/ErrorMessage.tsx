import Button from '@/components/ui/Button'

interface ErrorMessageProps {
  title?: string
  message?: string
  onRetry?: () => void
}

function ErrorMessage({ title = 'Something went wrong', message, onRetry }: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert">
      <p className="error-message__title">{title}</p>
      {message && <p className="error-message__detail">{message}</p>}
      {onRetry && (
        <Button type="button" variant="secondary" size="sm" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  )
}

export default ErrorMessage
