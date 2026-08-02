interface EmptyStateProps {
  title?: string
  message?: string
}

function EmptyState({ title = 'Nothing here yet', message }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <p className="empty-state__title">{title}</p>
      {message && <p className="empty-state__message">{message}</p>}
    </div>
  )
}

export default EmptyState
