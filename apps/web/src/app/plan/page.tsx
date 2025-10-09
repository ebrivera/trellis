'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { ChatMessage } from '../../components/ui/ChatMessage'
import { DebateViewer } from '../../components/ui/DebateViewer'
import { ApprovalDetailsModal } from '../../components/ui/ApprovalDetailsModal'
import { ApprovalPreviewCard } from '../../components/ui/ApprovalPreviewCard'
import type { ApprovalGate, AgentName, DebateMessage } from '@trellis/types'

type Message = {
    id: string
    role: 'user' | 'system'
    content: string
    streaming?: boolean
    approvalPreview?: ApprovalGate
    showActions?: boolean
    debateData?: {
        messages: Record<AgentName, DebateMessage[]>
        currentRound: 1 | 2 | 3
        winner?: AgentName
        voteTally?: Record<AgentName, number>
    }
}

const DEMO_TEMPLATES = [
    'Match 50 volunteers to 10 Sunday roles based on availability',
    'Track first-time visitors and flag ones we haven\'t contacted in 2 weeks',
    'Show giving trends by initiative with lapsed-donor alerts',
]

export default function GoalsPage() {
    const router = useRouter()
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'system',
            content: 'Hi! I\'m Foundry. Describe what you want to accomplish, and I\'ll help you create a structured plan with all the necessary steps.',
        },
    ])
    const [input, setInput] = useState('')
    const [isProcessing, setIsProcessing] = useState(false)
    const [currentApproval, setCurrentApproval] = useState<ApprovalGate | null>(null)
    const [csvUrls, setCsvUrls] = useState<Record<string, string>>({})
    const [showCsvInput, setShowCsvInput] = useState(false)
    const [csvFiles, setCsvFiles] = useState<Record<string, File>>({})
    const [dataSource, setDataSource] = useState<'url' | 'file'>('url')
    const [debateMessages, setDebateMessages] = useState<Record<AgentName, DebateMessage[]>>({
        Planner: [],
        Operations: [],
        HumanFlourishing: [],
        Moderator: []
    })
    const [currentRound, setCurrentRound] = useState<1 | 2 | 3>(1)
    const [winner, setWinner] = useState<AgentName | undefined>()
    const [voteTally, setVoteTally] = useState<Record<AgentName, number> | undefined>()
    const [showDetailsModal, setShowDetailsModal] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async () => {
        if (!input.trim() || isProcessing) return
    
        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
        }
    
        setMessages((prev) => [...prev, userMessage])
        setInput('')
        setIsProcessing(true)
    
        // Track winner locally for use in callbacks
        let debateWinner: AgentName | undefined
    
        // Reset debate state
        setDebateMessages({
            Planner: [],
            Operations: [],
            HumanFlourishing: [],
            Moderator: []
        })
        setCurrentRound(1)
        setWinner(undefined)
        setVoteTally(undefined)
    
        // Add "analyzing" message
        const analyzingMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'system',
            content: 'Analyzing your request...',
        }
        setMessages((prev) => [...prev, analyzingMessage])
    
        // Add debate message placeholder
        const debateMessageId = (Date.now() + 2).toString()
        const debateMessage: Message = {
            id: debateMessageId,
            role: 'system',
            content: 'Three agents are debating the best approach...',
            debateData: {
                messages: {
                    Planner: [],
                    Operations: [],
                    HumanFlourishing: [],
                    Moderator: []
                },
                currentRound: 1
            }
        }
        setMessages((prev) => [...prev, debateMessage])
    
        try {
            const eventSource = new EventSource(
                `http://localhost:8000/orchestrate/stream?${new URLSearchParams({
                    request: input
                })}`
            )
    
            eventSource.addEventListener('classifier_complete', (e) => {
                const data = JSON.parse(e.data)
                console.log('✅ Classified as:', data.template)
                
                // Remove analyzing message
                setMessages(prev => prev.filter(m => m.id !== analyzingMessage.id))
            })

            eventSource.addEventListener('clarification_needed', (e) => {
                const data = JSON.parse(e.data)
                console.log('❓ Clarification needed:', data.question)

                // Close SSE connection
                eventSource.close()

                // Remove analyzing and debate messages
                setMessages(prev => prev.filter(m =>
                    m.id !== analyzingMessage.id && m.id !== debateMessageId
                ))

                // Add clarification message
                const clarificationMessage: Message = {
                    id: Date.now().toString(),
                    role: 'system',
                    content: `I need some clarification before proceeding:\n\n${data.question}\n\nPlease provide more details so I can create the best plan for you.`,
                    streaming: true
                }
                setMessages(prev => [...prev, clarificationMessage])
                setIsProcessing(false)
            })

            eventSource.addEventListener('ethical_veto_total_rejection', (e) => {
                const data = JSON.parse(e.data)
                console.log('🚨 Ethical veto - total rejection:', data.agent)

                eventSource.close()
                setMessages(prev => prev.filter(m => m.id !== analyzingMessage.id))

                const ethicalMessage: Message = {
                    id: Date.now().toString(),
                    role: 'system',
                    content: data.concerns,
                    streaming: true
                }
                setMessages(prev => [...prev, ethicalMessage])
                setIsProcessing(false)
            })

            eventSource.addEventListener('ethical_veto_partial_rejection', (e) => {
                const data = JSON.parse(e.data)
                console.log('✏️ Ethical veto - partial rejection:', data.agent)

                eventSource.close()
                setMessages(prev => prev.filter(m => m.id !== analyzingMessage.id))

                const alternativeMessage: Message = {
                    id: Date.now().toString(),
                    role: 'system',
                    content: data.concerns,
                    streaming: true
                }
                setMessages(prev => [...prev, alternativeMessage])
                setIsProcessing(false)
            })
    
            eventSource.addEventListener('debate_start', (e) => {
                console.log('🎭 Debate starting...')
            })
    
            eventSource.addEventListener('round_1_proposal', (e) => {
                const data = JSON.parse(e.data)
                
                setMessages(prev => prev.map(msg => {
                    if (msg.id === debateMessageId && msg.debateData) {
                        return {
                            ...msg,
                            debateData: {
                                ...msg.debateData,
                                messages: {
                                    ...msg.debateData.messages,
                                    [data.agent as AgentName]: [
                                        ...msg.debateData.messages[data.agent as AgentName],
                                        data as DebateMessage
                                    ]
                                }
                            }
                        }
                    }
                    return msg
                }))
            })
    
            eventSource.addEventListener('round_2_rebuttal', (e) => {
                const data = JSON.parse(e.data)
                
                setMessages(prev => prev.map(msg => {
                    if (msg.id === debateMessageId && msg.debateData) {
                        return {
                            ...msg,
                            debateData: {
                                ...msg.debateData,
                                currentRound: 2,
                                messages: {
                                    ...msg.debateData.messages,
                                    [data.agent as AgentName]: [
                                        ...msg.debateData.messages[data.agent as AgentName],
                                        data as DebateMessage
                                    ]
                                }
                            }
                        }
                    }
                    return msg
                }))
            })
    
            eventSource.addEventListener('round_3_vote', (e) => {
                const data = JSON.parse(e.data)
                
                setMessages(prev => prev.map(msg => {
                    if (msg.id === debateMessageId && msg.debateData) {
                        return {
                            ...msg,
                            debateData: {
                                ...msg.debateData,
                                currentRound: 3,
                                messages: {
                                    ...msg.debateData.messages,
                                    [data.agent as AgentName]: [
                                        ...msg.debateData.messages[data.agent as AgentName],
                                        data as DebateMessage
                                    ]
                                }
                            }
                        }
                    }
                    return msg
                }))
            })
    
            eventSource.addEventListener('voting_complete', (e) => {
                const data = JSON.parse(e.data)
                
                // Store winner for later use
                debateWinner = data.winner
                setWinner(data.winner)
                setVoteTally(data.voteTally)
                
                setMessages(prev => prev.map(msg => {
                    if (msg.id === debateMessageId && msg.debateData) {
                        return {
                            ...msg,
                            debateData: {
                                ...msg.debateData,
                                winner: data.winner,
                                voteTally: data.voteTally
                            }
                        }
                    }
                    return msg
                }))
                
                console.log('🏆 Winner:', data.winner)
            })

            eventSource.addEventListener('preview_ready', async (e) => {
                const data = JSON.parse(e.data)
                
                // Close SSE connection
                eventSource.close()
                
                try {
                    // Fetch full approval details from database
                    const approvalResponse = await fetch(`http://localhost:8000/approval/${data.approvalId}`)
                    if (!approvalResponse.ok) {
                        throw new Error('Failed to fetch approval details')
                    }
                    const approval = await approvalResponse.json()
                    
                    // Parse JSON strings from database
                    const previewData = typeof approval.preview_data === 'string' 
                        ? JSON.parse(approval.preview_data) 
                        : approval.preview_data
                    
                    const metricsData = typeof approval.metrics === 'string'
                        ? JSON.parse(approval.metrics)
                        : approval.metrics

                    // Parse extracted_params from approval (already joined with workflow_run)
                    const extractedParams = typeof approval.extracted_params === 'string'
                        ? JSON.parse(approval.extracted_params)
                        : approval.extracted_params || {}

                    // Create clean display metrics based on template
                    let displayMetrics: Record<string, string | number> = {}
                    if (data.template === 'matching') {
                        displayMetrics = {
                            'Proposed Assignments': previewData.proposed_assignments || 0,
                            'Match Rate': `${Math.round((previewData.match_rate || 0) * 100)}%`,
                            'Avg Match Score': `${Math.round((previewData.avg_match_score || 0) * 100)}%`,
                            'Source Count': previewData.source_count || 0,
                            'Target Count': previewData.target_count || 0,
                        }
                    } else if (data.template === 'monitoring') {
                        displayMetrics = {
                            'Flagged Count': previewData.flagged_count || 0,
                            'Total Scanned': previewData.total_scanned || 0,
                            'Notifications Planned': previewData.notifications_planned || 0
                        }
                    } else if (data.template === 'analysis') {
                        displayMetrics = {
                            'Total Analyzed': previewData.total_analyzed || 0,
                            'Metrics Calculated': Object.keys(previewData.metrics_calculated || {}).length,
                            'Dimensions': previewData.dimensions?.length || 0
                        }
                    }
                    
                    // Add approval message (debate message stays in history!)
                    const approvalMessage: Message = {
                        id: (Date.now() + 3).toString(),
                        role: 'system',
                        content: `Debate complete! ${debateWinner || 'The winning agent'} won. Here's the preview:`,
                        approvalPreview: {
                            id: approval.id,
                            template: data.template,
                            status: approval.status,
                            createdAt: approval.created_at,
                            workflow_run_id: approval.workflow_run_id,
                            params: { sourceFile: 'default', ...extractedParams },
                            preview: previewData,
                            metrics: displayMetrics
                        },
                        showActions: true
                    }
                    
                    setMessages(prev => [...prev, approvalMessage])
                    setCurrentApproval({
                        id: approval.id,
                        template: data.template,
                        status: approval.status,
                        createdAt: approval.created_at,
                        workflow_run_id: approval.workflow_run_id,
                        params: { sourceFile: 'default', ...extractedParams },
                        preview: previewData,
                        metrics: displayMetrics
                    })
                    
                } catch (error) {
                    console.error('Error fetching approval details:', error)
                    // Fallback: use SSE data
                    const approvalMessage: Message = {
                        id: (Date.now() + 3).toString(),
                        role: 'system',
                        content: `Debate complete! ${debateWinner || 'The winning agent'} won. Here's the preview:`,
                        approvalPreview: {
                            id: data.approvalId,
                            template: data.template,
                            status: 'pending',
                            createdAt: new Date().toISOString(),
                            params: { sourceFile: 'default' },
                            preview: data.preview,
                            metrics: data.preview
                        },
                        showActions: true
                    }
                    setMessages(prev => [...prev, approvalMessage])
                }
                
                setIsProcessing(false)
            })
    
            eventSource.addEventListener('complete', (e) => {
                console.log('✅ Orchestration complete')
            })
    
            eventSource.addEventListener('error', (e: any) => {
                console.error('❌ SSE Error:', e)
                eventSource.close()
                
                const errorMessage: Message = {
                    id: Date.now().toString(),
                    role: 'system',
                    content: 'An error occurred during processing. Please try again.',
                }
                setMessages(prev => [...prev, errorMessage])
                setIsProcessing(false)
            })
    
        } catch (error) {
            console.error('Connection error:', error)
            setIsProcessing(false)
        }
    }

    const handleApprove = async () => {
        if (!currentApproval) return
        
        try {
            setIsProcessing(true)
            
            const response = await fetch(`http://localhost:8000/approval/${currentApproval.id}/decide`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'approve',
                    approved_by: 'user@church.org'
                })
            })
            
            if (!response.ok) {
                throw new Error('Failed to approve workflow')
            }
            
            const approvalMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: '✅ Workflow approved and executed successfully! Redirecting to results...',
            }
            setMessages((prev) => [...prev, approvalMessage])
            setCurrentApproval(null)
            
            setTimeout(() => {
                router.push('/approvals')
            }, 1500)
            
        } catch (error) {
            console.error('Error approving workflow:', error)
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: '❌ Failed to approve workflow. Please try again.',
            }
            setMessages((prev) => [...prev, errorMessage])
        } finally {
            setIsProcessing(false)
        }
    }

    const handleSaveForLater = async () => {
        if (!currentApproval) return

        const saveMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: '✓ Plan saved! You can review it later in the Approvals page.',
        }
        setMessages((prev) => [...prev, saveMessage])
        setCurrentApproval(null)
    }

    const handleViewDetails = () => {
        setShowDetailsModal(true)
    }

    const handleCancel = async () => {
        if (!currentApproval) return
        
        try {
            setIsProcessing(true)
            
            const response = await fetch(`http://localhost:8000/approval/${currentApproval.id}/decide`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'reject',
                    reason: 'Rejected via chat interface'
                })
            })
            
            if (!response.ok) {
                throw new Error('Failed to reject workflow')
            }
            
            const cancelMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: '❌ Plan rejected. Feel free to start a new goal whenever you\'re ready.',
            }
            setMessages((prev) => [...prev, cancelMessage])
            setCurrentApproval(null)
            
        } catch (error) {
            console.error('Error rejecting workflow:', error)
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: '❌ Failed to reject workflow. Please try again.',
            }
            setMessages((prev) => [...prev, errorMessage])
        } finally {
            setIsProcessing(false)
        }
    }

    const handleTemplate = (template: string) => {
        setInput(template)
    }

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <main className="flex flex-col min-h-screen px-6 pt-32 pb-6">
            <div className="flex flex-col flex-1 w-full mx-auto max-w-7xl">
                {/* Header */}
                <header className="mb-8">
                    <h1 className="mb-2 text-4xl font-bold text-white">Plan with Foundry</h1>
                    <p className="text-lg text-white/70">
                        Describe what you want to accomplish — Foundry will draft a plan for you.
                    </p>
                    <p className="mt-2 text-sm text-white/50">
                        e.g., &ldquo;Plan fall groups by ZIP, balance capacity, and draft leader/member messages&rdquo;
                    </p>
                </header>

                {/* Suggested Templates */}
                <div className="mb-6">
                    <p className="mb-3 text-sm font-medium text-white/70">Quick Start Templates:</p>
                    <div className="flex flex-wrap gap-2">
                        {DEMO_TEMPLATES.map((template, idx) => (
                            <button
                                key={idx}
                                onClick={() => handleTemplate(template)}
                                className="px-4 py-2 text-sm text-white transition-colors border rounded-full border-white/20 bg-white/5 hover:bg-white/10"
                            >
                                {template.slice(0, 40)}...
                            </button>
                        ))}
                    </div>
                </div>
                
                {/* CSV Upload Section - Placeholder for future */}
                <div className="mb-6">
                    <button
                        onClick={() => setShowCsvInput(!showCsvInput)}
                        className="text-sm transition-colors text-white/70 hover:text-white"
                    >
                        {showCsvInput ? '− Hide' : '+ Add'} CSV/Sheet URLs
                    </button>
                
                    {showCsvInput && (
                        <Card className="mt-3" padding="lg">
                            <h3 className="mb-3 font-semibold text-white">Upload Data Sources</h3>
                            <p className="text-sm text-white/50">
                                Coming soon: Upload your own data sources
                            </p>
                        </Card>
                    )}
                </div>

                {/* Chat Messages Container */}
                <Card className="flex flex-col flex-1 mb-6" padding="lg">
                    <div className="flex-1 mb-6 space-y-4 overflow-y-auto max-h-[600px]">
                        {messages.map((message) => (
                            <div key={message.id} className="space-y-4">
                                <ChatMessage role={message.role} streaming={message.streaming}>
                                    {message.content}
                                </ChatMessage>

                                {/* Debate Viewer */}
                                {message.debateData && (
                                    <div className="mt-4">
                                        <DebateViewer
                                            messages={message.debateData.messages}
                                            currentRound={message.debateData.currentRound}
                                            winner={message.debateData.winner}
                                            voteTally={message.debateData.voteTally}
                                        />
                                    </div>
                                )}

                                {/* Approval Preview */}
                                {message.approvalPreview && (
                                    <div className="mt-4">
                                        <ApprovalPreviewCard
                                            approval={message.approvalPreview}
                                            showActions={message.showActions || false}
                                            isProcessing={isProcessing}
                                            onApprove={handleApprove}
                                            onSaveForLater={handleSaveForLater}
                                            onViewDetails={handleViewDetails}
                                            onCancel={handleCancel}
                                        />
                                    </div>
                                )}
                            </div>
                        ))}

                        {isProcessing && (
                            <ChatMessage role="system">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 bg-white rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:0.2s]" />
                                    <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:0.4s]" />
                                    <span className="ml-2 text-white/70">Foundry is preparing your plan...</span>
                                </div>
                            </ChatMessage>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask Foundry to plan something..."
                            disabled={isProcessing}
                            className="flex-1 px-6 py-4 text-white transition-colors border placeholder-white/50 rounded-3xl bg-white/5 border-white/20 focus:outline-none focus:border-white/40 disabled:opacity-50"
                        />
                        <Button
                            onClick={handleSend}
                            disabled={!input.trim() || isProcessing}
                            size="lg"
                            className="px-8 shrink-0"
                        >
                            Send
                        </Button>
                    </div>
                </Card>

                {/* Details Modal */}
                <ApprovalDetailsModal
                    isOpen={showDetailsModal}
                    onClose={() => setShowDetailsModal(false)}
                    approval={currentApproval}
                    onApprove={handleApprove}
                    isProcessing={isProcessing}
                />
            </div>
        </main>
    )
}