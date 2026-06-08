import React from 'react'
import clsx from 'clsx'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
}

export function LoadingSpinner({ size = 'md', message }: LoadingSpinnerProps) {
  const sizeMap = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  }

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div
        className={clsx(
          'border-4 border-gray-200 border-t-purple-600 rounded-full animate-spin',
          sizeMap[size]
        )}
      />
      {message && <p className="text-gray-600">{message}</p>}
    </div>
  )
}
