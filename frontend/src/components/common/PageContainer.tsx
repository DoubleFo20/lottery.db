import type { ReactNode } from 'react'

interface PageContainerProps {
  title?: string
  description?: string
  children: ReactNode
}

function PageContainer({ title, description, children }: PageContainerProps) {
  return (
    <section className="page-container">
      {title && <h1 className="page-container__title">{title}</h1>}
      {description && <p className="page-container__description">{description}</p>}
      <div className="page-container__content">{children}</div>
    </section>
  )
}

export default PageContainer
