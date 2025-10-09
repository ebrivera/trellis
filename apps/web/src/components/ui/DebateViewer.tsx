'use client'

import { useState, useEffect, useRef } from 'react'
import { Card } from './Card'
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
    const [expandedAgent, setExpandedAgent] = useState<AgentName | null>(null)
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
                                isWinner ? 'ring-2 ring-yellow-400' : ''
                            }`}
                            style={{ minHeight: '200px' }}
                        >
                            {/* Agent Header */}
                            <div className="mb-4">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className="text-2xl">{config.emoji}</span>
                                        <h4 className={`font-bold ${config.color}`}>
                                            {agent}
                                        </h4>
                                    </div>
                                    {isWinner && (
                                        <Badge variant="warning">
                                            🏆 Winner
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
                                        const isExpanded = expandedAgent === agent
                                        const isTruncated = msg.content.length > 200
                                        const displayContent = isExpanded || !isTruncated 
                                            ? msg.content 
                                            : `${msg.content.slice(0, 200)}...`

                                        return (
                                            <div 
                                                key={idx}
                                                className="p-3 border rounded-lg bg-white/5 border-white/10 animate-fadeIn"
                                            >
                                                <div className="mb-1 text-xs font-medium text-white/70">
                                                    Round {msg.round}: {msg.messageType}
                                                </div>
                                                <p className="text-sm text-white/90">
                                                    {displayContent}
                                                </p>
                                                {isTruncated && (
                                                    <button
                                                        onClick={() => setExpandedAgent(isExpanded ? null : agent)}
                                                        className="mt-2 text-xs text-blue-400 hover:text-blue-300"
                                                    >
                                                        {isExpanded ? '− Show less' : '+ Show more'}
                                                    </button>
                                                )}
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
                <div className="text-center mb-3">
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