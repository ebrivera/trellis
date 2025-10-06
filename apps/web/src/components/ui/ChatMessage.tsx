import { ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface ChatMessageProps {
  role: 'user' | 'system'
  children: ReactNode
  className?: string
}

export function ChatMessage({ role, children, className }: ChatMessageProps) {
  return (
    <div
      className={cn(
        'flex w-full',
        role === 'user' ? 'justify-end' : 'justify-start',
        className
      )}
    >
      <div
        className={cn(
          'max-w-[85%] rounded-3xl px-6 py-4',
          role === 'user'
            ? 'bg-white text-black'
            : 'bg-white/10 backdrop-blur-xl border border-white/20 text-white'
        )}
      >
        {children}
      </div>
    </div>
  )
}

export default ChatMessage

