import { ReactNode, HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    children: ReactNode
    className?: string
    padding?: 'none' | 'sm' | 'md' | 'lg'
    rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl'
    variant?: 'glass' | 'solid' | 'outline'
}

const paddingMap = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
}

const roundedMap = {
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    '3xl': 'rounded-3xl',
}

const variantMap = {
    glass: 'bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl shadow-black/10',
    solid: 'bg-white border border-gray-200 shadow-lg',
    outline: 'border-2 border-white/30',
}

export function Card({
    children,
    className,
    padding = 'md',
    rounded = '3xl',
    variant = 'glass',
    ...props
}: CardProps) {
    return (
        <div
            className={cn(
                paddingMap[padding],
                roundedMap[rounded],
                variantMap[variant],
                className
            )}
            {...props}
        >
        {children}
        </div>
    )
}

export default Card

