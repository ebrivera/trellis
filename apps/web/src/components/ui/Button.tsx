import { ReactNode, ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const variantMap = {
  primary: 'bg-white text-black hover:bg-gray-100',
  secondary: 'bg-black text-white hover:bg-gray-800',
  ghost: 'bg-transparent text-white hover:bg-white/10',
  outline: 'bg-transparent border-2 border-white text-white hover:bg-white/10',
}

const sizeMap = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-3xl font-medium transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100',
        variantMap[variant],
        sizeMap[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export default Button

