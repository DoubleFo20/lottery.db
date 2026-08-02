interface LoadingSpinnerProps {
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

function LoadingSpinner({ label = 'Loading...', size = 'md' }: LoadingSpinnerProps) {
  return (
    <div className={`loading loading--${size}`} role="status">
      <span className="loading__spinner" aria-hidden="true" />
      <span className="loading__label">{label}</span>
    </div>
  )
}

export default LoadingSpinner
