import { ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'warning' | 'success' | 'danger' | 'info'
  className?: string
}

const variantMap = {
  default: 'bg-white/10 text-white border-white/20',
  warning: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/30',
  success: 'bg-green-400/10 text-green-400 border-green-400/30',
  danger: 'bg-red-400/10 text-red-400 border-red-400/30',
  info: 'bg-blue-400/10 text-blue-400 border-blue-400/30',
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-3 py-1 text-xs font-medium border rounded-full',
        variantMap[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

export default Badge

