import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
  children: ReactNode
}

function Card({ title, children, className = '', ...rest }: CardProps) {
  return (
    <div className={`card${className ? ` ${className}` : ''}`} {...rest}>
      {title && <h3 className="card__title">{title}</h3>}
      <div className="card__body">{children}</div>
    </div>
  )
}

export default Card
