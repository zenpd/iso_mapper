import React from 'react'
import clsx from 'clsx'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  subtitle?: string
  variant?: 'default' | 'elevated'
}

export function Card({
  title,
  subtitle,
  variant = 'default',
  className,
  children,
  ...props
}: CardProps) {
  const baseStyles = 'rounded-lg'
  
  const variantStyles = {
    default: 'bg-white border border-gray-200',
    elevated: 'bg-white shadow-lg',
  }

  return (
    <div className={clsx(baseStyles, variantStyles[variant], className)} {...props}>
      {title && (
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}
