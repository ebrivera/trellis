'use client'

import { useState, useEffect, useRef } from 'react'
import { Card } from './Card'
import { Badge } from './Badge'
import { StreamingText } from './StreamingText'
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
    1: 'proposal',
    2: 'rebuttal',
    3: 'vote'
}

interface DebateViewerProps {
    messages: Record<AgentName, DebateMessage[]>
    currentRound: 1 | 2 | 3
    winner?: AgentName
    voteTally?: Record<AgentName, number>
}

export function DebateViewer({ messages, currentRound, winner, voteTally }: DebateViewerProps) {
    const agents: AgentName[] = ['Planner', 'Operations', 'HumanFlourishing']
    const [selectedRound, setSelectedRound] = useState<1 | 2 | 3>(currentRound)
    const [modalMessage, setModalMessage] = useState<{ agent: AgentName; message: DebateMessage } | null>(null)
    const prevCurrentRound = useRef(currentRound)

    // Update selected round when current round changes (but only forward, not backward)
    useEffect(() => {
        if (currentRound > prevCurrentRound.current) {
            setSelectedRound(currentRound)
        }
        prevCurrentRound.current = currentRound
    }, [currentRound])
    
    return (
        <Card padding="lg" className="bg-white/5">
            {/* Header */}
            <div className="mb-6">
                <h3 className="mb-2 text-xl font-bold text-white">
                    Multi-Agent Debate in Progress
                </h3>
                <p className="text-sm text-white/70">
                    Three agents are evaluating the best approach for your request
                </p>
            </div>

            {/* 3-Column Layout */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {agents.map(agent => {
                    const config = AGENT_CONFIGS[agent]
                    const agentMessages = messages[agent] || []
                    const isWinner = winner === agent
                    const votes = voteTally?.[agent] || 0

                    // Filter messages for selected round
                    const roundMessages = agentMessages.filter(msg => msg.round === selectedRound)
                    const hasMessages = roundMessages.length > 0

                    return (
                        <div 
                            key={agent}
                            className={`flex flex-col border rounded-lg p-4 transition-all ${config.bgColor} ${config.borderColor} ${
                                isWinner ? 'ring-4 ring-yellow-400/60 animate-winnerGlow animate-winnerPulse relative overflow-hidden' : ''
                            }`}
                            style={{ minHeight: '200px' }}
                        >
                            {/* Winner shimmer overlay */}
                            {isWinner && (
                                <div className="absolute inset-0 pointer-events-none animate-winnerShimmer" />
                            )}
                            {/* Agent Header */}
                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className={`text-2xl ${isWinner ? 'drop-shadow-[0_0_8px_rgba(255,215,0,0.8)]' : ''}`}>
                                            {config.emoji}
                                        </span>
                                        <h4 className={`font-bold ${config.color} ${isWinner ? 'drop-shadow-[0_0_8px_rgba(255,215,0,0.6)]' : ''}`}>
                                            {agent}
                                        </h4>
                                    </div>
                                    {isWinner && (
                                        <Badge 
                                            variant="warning"
                                            className="relative overflow-hidden animate-badgeBounce"
                                        >
                                            <span className="relative z-10 flex items-center gap-1">
                                                <span className="animate-spin">🏆</span>
                                                Winner
                                            </span>
                                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-yellow-400/30 to-transparent animate-winnerShimmer" />
                                        </Badge>
                                    )}
                                </div>
                                <p className="text-xs text-white/50">
                                    {config.description}
                                </p>
                            </div>

                            {/* Messages for selected round */}
                            <div className="flex-1">
                                {hasMessages ? (
                                    roundMessages.map((msg, idx) => {
                                        // Stream if this is the latest message in the current round
                                        const isLatestMessage = idx === roundMessages.length - 1
                                        const isCurrentRound = msg.round === currentRound
                                        const shouldStream = isLatestMessage && isCurrentRound && selectedRound === currentRound

                                        return (
                                            <div
                                                key={idx}
                                                className="p-3 border rounded-lg bg-white/5 border-white/10 animate-fadeIn"
                                            >
                                                <div className="mb-1 text-xs font-medium text-white/70">
                                                    Round {msg.round}: {msg.messageType}
                                                </div>
                                                <div className="text-sm whitespace-pre-wrap text-white/90">
                                                    {shouldStream ? (
                                                        <StreamingText text={msg.content} speed={15} />
                                                    ) : (
                                                        msg.content
                                                    )}
                                                </div>
                                            </div>
                                        )
                                    })
                                ) : (
                                    <div className="flex items-center justify-center h-full text-sm text-white/30">
                                        Waiting for {ROUND_LABELS[selectedRound]}...
                                    </div>
                                )}
                            </div>

                            {/* Vote Count (only show in round 3) */}
                            {selectedRound === 3 && votes > 0 && (
                                <div className="pt-3 mt-3 border-t border-white/10">
                                    <div className="text-xs text-center text-white/70">
                                        {votes} vote{votes !== 1 ? 's' : ''}
                                    </div>
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Round Navigation */}
            <div className="mt-6">
                <div className="mb-3 text-center">
                    <p className="text-sm text-white/70">
                        Navigate between debate rounds to see what each agent was thinking
                    </p>
                </div>
                <div className="flex items-center justify-center gap-2">
                    {[1, 2, 3].map(round => {
                        const roundNum = round as 1 | 2 | 3
                        const isActive = selectedRound === roundNum
                        const isComplete = currentRound > roundNum
                        const isAvailable = currentRound >= roundNum
                        
                        return (
                            <button
                                key={round}
                                onClick={() => isAvailable && setSelectedRound(roundNum)}
                                disabled={!isAvailable}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                                    isActive
                                        ? 'bg-white text-black'
                                        : isComplete
                                        ? 'bg-green-400/20 text-green-400 hover:bg-green-400/30 cursor-pointer'
                                        : isAvailable
                                        ? 'bg-white/10 text-white/50'
                                        : 'bg-white/5 text-white/30 cursor-not-allowed'
                                }`}
                            >
                                Round {round}
                            </button>
                        )
                    })}
                </div>
            </div>
        </Card>
    )
}