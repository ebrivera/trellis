'use client'

import { useEffect } from 'react'
import { Badge } from './Badge'
import type { AgentName, DebateMessage } from '@trellis/types'

const AGENT_CONFIGS: Record<AgentName, {
    emoji: string
    color: string
    bgColor: string
    borderColor: string
    description: string
}> = {
    Planner: {
        emoji: '📊',
        color: 'text-blue-400',
        bgColor: 'bg-blue-400/10',
        borderColor: 'border-blue-400/20',
        description: 'Efficiency & Scalability'
    },
    Operations: {
        emoji: '⚙️',
        color: 'text-orange-400',
        bgColor: 'bg-orange-400/10',
        borderColor: 'border-orange-400/20',
        description: 'Feasibility & Execution'
    },
    HumanFlourishing: {
        emoji: '🌱',
        color: 'text-green-400',
        bgColor: 'bg-green-400/10',
        borderColor: 'border-green-400/20',
        description: 'Relationships & Growth'
    },
    Moderator: {
        emoji: '⚖️',
        color: 'text-purple-400',
        bgColor: 'bg-purple-400/10',
        borderColor: 'border-purple-400/20',
        description: 'Tie-Breaking Authority'
    }
}

const ROUND_LABELS: Record<1 | 2 | 3, string> = {
    1: 'Proposal',
    2: 'Rebuttal', 
    3: 'Vote'
}

interface DebateMessageModalProps {
    isOpen: boolean
    onClose: () => void
    agent: AgentName
    message: DebateMessage
}

export function DebateMessageModal({ isOpen, onClose, agent, message }: DebateMessageModalProps) {
    const config = AGENT_CONFIGS[agent]
    
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden'
        } else {
            document.body.style.overflow = 'unset'
        }
        return () => {
            document.body.style.overflow = 'unset'
        }
    }, [isOpen])

    if (!isOpen) return null
    
    return (
        <div
            className="fixed inset-0 z-[100] flex items-center justify-center px-4 bg-black/60 rounded-3xl"
            onClick={onClose}
        >
            <div
                className="w-full max-w-md max-h-[60vh] bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden"
                onClick={(e: React.MouseEvent) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-3 border-b border-gray-700">
                    <div className="flex items-center gap-2">
                        <span className="text-lg">{config.emoji}</span>
                        <div>
                            <h2 className="text-base font-semibold text-white">{agent}</h2>
                            <p className="text-xs text-gray-400">{ROUND_LABELS[message.round]}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="p-3 overflow-y-auto max-h-[calc(60vh-60px)]">
                    <div className="mb-2">
                        <Badge variant="default" className="text-xs">
                            {message.messageType}
                        </Badge>
                    </div>
                    <div className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
                        {message.content}
                    </div>
                </div>
            </div>
        </div>
    )
}
