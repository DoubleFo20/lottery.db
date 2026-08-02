import { Component, type ErrorInfo, type ReactNode } from 'react'
import ErrorMessage from '@/components/common/ErrorMessage'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  message: string
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, message: '' }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, info)
  }

  private handleReset = () => {
    this.setState({ hasError: false, message: '' })
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorMessage
          title="Application error"
          message={this.state.message}
          onRetry={this.handleReset}
        />
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
