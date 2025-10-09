import { ReactNode } from 'react'
import { cn } from '../../lib/utils'
import { StreamingText } from './StreamingText'

interface ChatMessageProps {
  role: 'user' | 'system'
  children: ReactNode
  className?: string
  streaming?: boolean
}

export function ChatMessage({ role, children, className, streaming = false }: ChatMessageProps) {
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
        {streaming && typeof children === 'string' ? (
          <StreamingText text={children} speed={15} />
        ) : (
          children
        )}
      </div>
    </div>
  )
}

export default ChatMessage

