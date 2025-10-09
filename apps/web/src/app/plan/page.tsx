'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { ChatMessage } from '../../components/ui/ChatMessage'
import { DebateViewer } from '../../components/ui/DebateViewer'
import { CheckCircle, Eye, X, Users, Clock, TrendingUp, AlertTriangle, Save } from 'lucide-react'
import type { ApprovalGate, MatchingPreview, MonitoringPreview, AnalysisPreview, AgentName, DebateMessage } from '@trellis/types'
// MOCK: Import mock data - backend will replace with API calls
// import { mockMatchingApproval, mockMonitoringApproval, mockAnalysisApproval } from '../../lib/mockData'

type Message = {
    id: string
    role: 'user' | 'system'
    content: string
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
            content: 'Hi! I\'m Trellis. Describe what you want to accomplish, and I\'ll help you create a structured plan with all the necessary steps.',
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
    // REMOVED: const [showDebate, setShowDebate] = useState(false)
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

                // Close SSE connection - no debate will happen
                eventSource.close()

                // Remove analyzing and debate messages
                setMessages(prev => prev.filter(m =>
                    m.id !== analyzingMessage.id && m.id !== debateMessageId
                ))

                // Add clarification message
                const clarificationMessage: Message = {
                    id: Date.now().toString(),
                    role: 'system',
                    content: `I need some clarification before proceeding:\n\n${data.question}\n\nPlease provide more details so I can create the best plan for you.`
                }
                setMessages(prev => [...prev, clarificationMessage])
                setIsProcessing(false)
            })

            eventSource.addEventListener('debate_start', (e) => {
                console.log('🎭 Debate starting...')
            })
    
            // Update debate message as proposals come in
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

            eventSource.addEventListener('ethical_veto_total_rejection', (e) => {
                const data = JSON.parse(e.data)
                console.log('🚨 Ethical veto - total rejection:', data.agent)

                // Close SSE connection - no execution will happen
                eventSource.close()

                // Remove "analyzing" message if it still exists
                setMessages(prev => prev.filter(m => m.id !== analyzingMessage.id))

                // Add ethical concerns message
                // The backend already formatted this message nicely, just display it
                const ethicalMessage: Message = {
                    id: Date.now().toString(),
                    role: 'system',
                    content: data.concerns
                }
                setMessages(prev => [...prev, ethicalMessage])
                setIsProcessing(false)
            })

            eventSource.addEventListener('ethical_veto_partial_rejection', (e) => {
                const data = JSON.parse(e.data)
                console.log('✏️ Ethical veto - partial rejection:', data.agent)

                // Close SSE connection - no execution will happen
                eventSource.close()

                // Remove "analyzing" message if it still exists
                setMessages(prev => prev.filter(m => m.id !== analyzingMessage.id))

                // Add alternative approach message
                // The backend already formatted this message nicely, just display it
                const alternativeMessage: Message = {
                    id: Date.now().toString(),
                    role: 'system',
                    content: data.concerns
                }
                setMessages(prev => [...prev, alternativeMessage])
                setIsProcessing(false)
            })

            eventSource.addEventListener('preview_ready', async (e) => {
                const data = JSON.parse(e.data)
                
                // Close SSE connection
                eventSource.close()
                
                // Fetch full approval details
                const approvalResponse = await fetch(`http://localhost:8000/approval/${data.approvalId}`)
                const approval = await approvalResponse.json()
                
                // Extract numeric metrics based on template
                let numericMetrics: Record<string, number> = {}
                if (data.template === 'matching') {
                    numericMetrics = {
                        'Proposed Assignments': data.preview.proposed_assignments,
                        'Match Rate': Math.round(data.preview.match_rate * 100),
                        'Avg Match Score': Math.round(data.preview.avg_match_score * 100),
                        'Notifications Planned': data.preview.notifications_planned
                    }
                } else if (data.template === 'monitoring') {
                    numericMetrics = {
                        'Flagged Count': data.preview.flagged_count,
                        'Total Scanned': data.preview.total_scanned,
                        'Notifications Planned': data.preview.notifications_planned
                    }
                } else if (data.template === 'analysis') {
                    numericMetrics = {
                        'Total Analyzed': data.preview.total_analyzed || 0,
                        'Metrics Calculated': Object.keys(data.preview.metrics || {}).length,
                        'Dimensions': data.preview.dimensions?.length || 0
                    }
                }
                
                // Add approval message (debate message stays in history!)
                const approvalMessage: Message = {
                    id: (Date.now() + 3).toString(),
                    role: 'system',
                    content: `Debate complete! ${debateWinner || 'The winning agent'} won. Here's the preview:`,
                    approvalPreview: {
                        id: data.approvalId,
                        template: data.template,
                        status: 'pending',
                        createdAt: new Date().toISOString(),
                        params: {
                            sourceFile: 'volunteers',
                            targetFile: 'roles'
                        },
                        preview: data.preview,
                        metrics: numericMetrics
                    },
                    showActions: true
                }
                
                setMessages(prev => [...prev, approvalMessage])
                setCurrentApproval({
                    id: data.approvalId,
                    template: data.template,
                    status: 'pending',
                    createdAt: new Date().toISOString(),
                    params: {
                        sourceFile: 'volunteers',
                        targetFile: 'roles'
                    },
                    preview: data.preview,
                    metrics: numericMetrics
                })
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

        // Execute the workflow
        try {
            await fetch(`http://localhost:8000/approval/${currentApproval.id}/decide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'approve' })
            })

            const approvalMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: 'Plan approved and executing! Redirecting to the Approvals page...',
            }
            setMessages((prev) => [...prev, approvalMessage])
            setCurrentApproval(null)

            setTimeout(() => {
                router.push('/approvals')
            }, 1000)
        } catch (error) {
            console.error('Failed to approve workflow:', error)
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: 'Failed to execute plan. Please try again.',
            }
            setMessages((prev) => [...prev, errorMessage])
        }
    }

    const handleSaveForLater = async () => {
        if (!currentApproval) return

        // Update status to 'saved' in backend
        try {
            await fetch(`http://localhost:8000/approval/${currentApproval.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'saved' })
            })

            const saveMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: '✓ Plan saved! You can review it later in the Approvals page. Feel free to create another plan.',
            }
            setMessages((prev) => [...prev, saveMessage])
            setCurrentApproval(null)
        } catch (error) {
            console.error('Failed to save approval:', error)
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: 'Failed to save plan. Please try again.',
            }
            setMessages((prev) => [...prev, errorMessage])
        }
    }

    const handleViewDetails = () => {
        setShowDetailsModal(true)
    }

    const handleCancel = async () => {
        if (!currentApproval) return

        // Reject the approval
        try {
            await fetch(`http://localhost:8000/approval/${currentApproval.id}/decide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'reject' })
            })

            const cancelMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: 'Plan rejected. Feel free to start a new goal whenever you\'re ready.',
            }
            setMessages((prev) => [...prev, cancelMessage])
            setCurrentApproval(null)
        } catch (error) {
            console.error('Failed to reject approval:', error)
            const errorMessage: Message = {
                id: Date.now().toString(),
                role: 'system',
                content: 'Failed to reject plan. Please try again.',
            }
            setMessages((prev) => [...prev, errorMessage])
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
                    <h1 className="mb-2 text-4xl font-bold text-white">Plan with Trellis</h1>
                    <p className="text-lg text-white/70">
                        Describe what you want to accomplish — Trellis will draft a plan for you.
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
                
                {/* CSV Upload Section */}
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
                        
                            {/* Toggle */}
                            <div className="flex gap-2 mb-4">
                                <button
                                    onClick={() => setDataSource('url')}
                                    className={`px-4 py-2 rounded-lg transition-colors ${
                                        dataSource === 'url' 
                                        ? 'bg-white text-black' 
                                        : 'bg-white/5 text-white/70 hover:bg-white/10'
                                    }`}
                                >
                                    Google Sheets URL
                                </button>
                                <button
                                    onClick={() => setDataSource('file')}
                                    className={`px-4 py-2 rounded-lg transition-colors ${
                                        dataSource === 'file' 
                                        ? 'bg-white text-black' 
                                        : 'bg-white/5 text-white/70 hover:bg-white/10'
                                    }`}
                                >
                                    Upload CSV File
                                </button>
                            </div>

                            <div className="space-y-3">
                                {/* Source */}
                                <div>
                                    <label className="block mb-1 text-sm text-white/70">
                                        Source File (e.g., volunteers, visitors, gifts)
                                    </label>
                                    {dataSource === 'url' ? (
                                        <input
                                            type="text"
                                            placeholder="https://docs.google.com/spreadsheets/d/..."
                                            value={csvUrls.source || ''}
                                            onChange={(e) => setCsvUrls(prev => ({ ...prev, source: e.target.value }))}
                                            className="w-full px-4 py-2 text-white border rounded-lg bg-white/5 border-white/20 placeholder-white/30 focus:outline-none focus:border-white/40"
                                        />
                                    ) : (
                                        <input
                                            type="file"
                                            accept=".csv,.xlsx"
                                            onChange={(e) => {
                                                const file = e.target.files?.[0]
                                                if (file) setCsvFiles(prev => ({ ...prev, source: file }))
                                            }}
                                            className="w-full px-4 py-2 text-white border rounded-lg bg-white/5 border-white/20 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-white/10 file:text-white hover:file:bg-white/20"
                                        />
                                    )}
                                    {csvFiles.source && (
                                        <p className="mt-1 text-sm text-green-400">
                                            ✓ {csvFiles.source.name}
                                        </p>
                                    )}
                                </div>

                                {/* Target */}
                                <div>
                                    <label className="block mb-1 text-sm text-white/70">
                                        Target File (optional - for matching only)
                                    </label>
                                    {dataSource === 'url' ? (
                                        <input
                                            type="text"
                                            placeholder="https://docs.google.com/spreadsheets/d/..."
                                            value={csvUrls.target || ''}
                                            onChange={(e) => setCsvUrls(prev => ({ ...prev, target: e.target.value }))}
                                            className="w-full px-4 py-2 text-white border rounded-lg bg-white/5 border-white/20 placeholder-white/30 focus:outline-none focus:border-white/40"
                                        />
                                    ) : (
                                        <input
                                            type="file"
                                            accept=".csv,.xlsx"
                                            onChange={(e) => {
                                                const file = e.target.files?.[0]
                                                if (file) setCsvFiles(prev => ({ ...prev, target: file }))
                                            }}
                                            className="w-full px-4 py-2 text-white border rounded-lg bg-white/5 border-white/20 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-white/10 file:text-white hover:file:bg-white/20"
                                        />
                                    )}
                                    {csvFiles.target && (
                                        <p className="mt-1 text-sm text-green-400">
                                            ✓ {csvFiles.target.name}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </Card>
                    )}
                </div>

                {/* Chat Messages Container */}
                <Card className="flex flex-col flex-1 mb-6" padding="lg">
                    <div className="flex-1 mb-6 space-y-4 overflow-y-auto max-h-[600px]">
                        {messages.map((message) => (
                            <div key={message.id} className="space-y-4">
                                <ChatMessage role={message.role}>
                                    {message.content}
                                </ChatMessage>

                                {/* Debate Viewer - INSIDE MESSAGES */}
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
                                        <Card padding="lg" className="space-y-4 bg-white/5">
                                            {/* Header with template badge */}
                                            <div className="flex items-center justify-between gap-3">
                                                <div className="flex items-center gap-3">
                                                    <Badge variant={message.approvalPreview.template === 'matching' ? 'info' : message.approvalPreview.template === 'monitoring' ? 'default' : 'success'}>
                                                        {message.approvalPreview.template.charAt(0).toUpperCase() + message.approvalPreview.template.slice(1)} Template
                                                    </Badge>
                                                    <h3 className="text-xl font-bold text-white">
                                                        {message.approvalPreview.template === 'matching' && `Match ${(message.approvalPreview.preview as MatchingPreview).assignments_preview?.length || 0} assignments`}
                                                        {message.approvalPreview.template === 'monitoring' && `Monitor ${(message.approvalPreview.preview as MonitoringPreview).flagged_count || 0} flagged entities`}
                                                        {message.approvalPreview.template === 'analysis' && `Analyze ${(message.approvalPreview.preview as AnalysisPreview).total_analyzed || 0} records`}
                                                    </h3>
                                                </div>
                                                <span className="px-3 py-1 text-xs font-medium text-yellow-400 border rounded-full border-yellow-400/30 bg-yellow-400/10 shrink-0">
                                                    Requires Approval
                                                </span>
                                            </div>

                                            {/* Template-specific preview summary */}
                                            <div className="p-4 border rounded-lg bg-white/5 border-white/10">
                                                <div className="flex items-start gap-3 mb-3">
                                                    {message.approvalPreview.template === 'matching' && <Users className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />}
                                                    {message.approvalPreview.template === 'monitoring' && <Clock className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />}
                                                    {message.approvalPreview.template === 'analysis' && <TrendingUp className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />}
                                                    <div className="flex-1">
                                                        <p className="mb-2 text-sm text-white/80">
                                                            {message.approvalPreview.template === 'matching' && `${(message.approvalPreview.preview as MatchingPreview).assignments_preview?.length || 0} proposed assignments from ${message.approvalPreview.params.sourceFile}${message.approvalPreview.params.targetFile ? ` to ${message.approvalPreview.params.targetFile}` : ''}`}
                                                            {message.approvalPreview.template === 'monitoring' && `${(message.approvalPreview.preview as MonitoringPreview).flagged_count || 0} entities flagged based on time conditions`}
                                                            {message.approvalPreview.template === 'analysis' && `Analysis of ${(message.approvalPreview.preview as AnalysisPreview).total_analyzed || 0} records with ${Object.keys((message.approvalPreview.preview as AnalysisPreview).metrics || {}).length} calculated metrics`}
                                                        </p>
                                                        {/* Show key metrics */}
                                                        <div className="flex flex-wrap gap-3 text-xs">
                                                            {Object.entries(message.approvalPreview.metrics)
                                                                .filter(([key, value]) => typeof value === 'number' || typeof value === 'string')
                                                                .slice(0, 3)
                                                                .map(([key, value]) => (
                                                                    <div key={key} className="flex items-center gap-1">
                                                                        <span className="text-white/50">{key}:</span>
                                                                        <span className="font-semibold text-white">{value}</span>
                                                                    </div>
                                                                ))}
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Warnings/Unmatched items */}
                                                {message.approvalPreview.template === 'matching' && 
                                                (message.approvalPreview.preview as MatchingPreview).unmatched && 
                                                ((message.approvalPreview.preview as MatchingPreview).unmatched?.length || 0) > 0 && (
                                                    <div className="flex items-start gap-2 p-2 mt-2 border rounded bg-yellow-400/10 border-yellow-400/20">
                                                        <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                                                        <p className="text-xs text-yellow-300">
                                                            {(message.approvalPreview.preview as MatchingPreview).unmatched?.length || 0} items couldn&apos;t be matched
                                                        </p>
                                                    </div>
                                                )}
                                            </div>

                                            {message.showActions && (
                                                <div className="flex flex-wrap gap-3 pt-4">
                                                    <Button onClick={handleApprove} size="lg">
                                                        <CheckCircle className="inline-block w-5 h-5 mr-2" />
                                                        Approve & Execute
                                                    </Button>
                                                    <Button onClick={handleSaveForLater} variant="outline" size="lg">
                                                        <Save className="inline-block w-5 h-5 mr-2" />
                                                        Save for Later
                                                    </Button>
                                                    <Button onClick={handleViewDetails} variant="outline" size="lg">
                                                        <Eye className="inline-block w-5 h-5 mr-2" />
                                                        View Details
                                                    </Button>
                                                    <Button onClick={handleCancel} variant="ghost" size="lg">
                                                        <X className="inline-block w-5 h-5 mr-2" />
                                                        Reject
                                                    </Button>
                                                </div>
                                            )}
                                        </Card>
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
                                    <span className="ml-2 text-white/70">Trellis is preparing your plan...</span>
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
                            placeholder="Ask Trellis to plan something..."
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
                {showDetailsModal && currentApproval && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setShowDetailsModal(false)}>
                        <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-gray-900 to-black border border-white/20 rounded-2xl" onClick={(e) => e.stopPropagation()}>
                            {/* Modal Header */}
                            <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b bg-gray-900/95 backdrop-blur-sm border-white/10">
                                <div className="flex items-center gap-3">
                                    <Badge variant={currentApproval.template === 'matching' ? 'info' : currentApproval.template === 'monitoring' ? 'default' : 'success'}>
                                        {currentApproval.template.charAt(0).toUpperCase() + currentApproval.template.slice(1)}
                                    </Badge>
                                    <h2 className="text-2xl font-bold text-white">Plan Details</h2>
                                </div>
                                <button
                                    onClick={() => setShowDetailsModal(false)}
                                    className="p-2 text-white transition-colors rounded-lg hover:bg-white/10"
                                >
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            {/* Modal Content */}
                            <div className="p-6 space-y-6">
                                {/* Metrics Overview */}
                                <div>
                                    <h3 className="mb-3 text-lg font-semibold text-white">Overview</h3>
                                    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                                        {Object.entries(currentApproval.metrics).map(([key, value]) => (
                                            <div key={key} className="p-4 border rounded-lg bg-white/5 border-white/10">
                                                <p className="mb-1 text-sm text-white/60">{key}</p>
                                                <p className="text-2xl font-bold text-white">{value}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Matching Template Details */}
                                {currentApproval.template === 'matching' && (
                                    <div>
                                        <h3 className="mb-3 text-lg font-semibold text-white">Proposed Assignments</h3>
                                        <div className="overflow-hidden border rounded-lg border-white/10">
                                            <table className="w-full">
                                                <thead className="bg-white/5">
                                                    <tr>
                                                        <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Source</th>
                                                        <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Target</th>
                                                        <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Match Score</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {(currentApproval.preview as MatchingPreview).assignments_preview?.slice(0, 10).map((assignment, idx) => (
                                                        <tr key={idx} className="border-t border-white/10">
                                                            <td className="px-4 py-3 text-sm text-white">{assignment.source_name}</td>
                                                            <td className="px-4 py-3 text-sm text-white">{assignment.target_name}</td>
                                                            <td className="px-4 py-3 text-sm text-white">
                                                                <span className="px-2 py-1 text-xs font-medium rounded bg-blue-400/20 text-blue-400">
                                                                    {Math.round((assignment.match_score || 0) * 100)}%
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                        {(currentApproval.preview as MatchingPreview).assignments_preview &&
                                         (currentApproval.preview as MatchingPreview).assignments_preview.length > 10 && (
                                            <p className="mt-2 text-sm text-white/50">
                                                Showing 10 of {(currentApproval.preview as MatchingPreview).assignments_preview.length} assignments
                                            </p>
                                        )}
                                    </div>
                                )}

                                {/* Monitoring Template Details */}
                                {currentApproval.template === 'monitoring' && (
                                    <div>
                                        <h3 className="mb-3 text-lg font-semibold text-white">Flagged Entities</h3>
                                        <div className="overflow-hidden border rounded-lg border-white/10">
                                            <table className="w-full">
                                                <thead className="bg-white/5">
                                                    <tr>
                                                        <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Name</th>
                                                        <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Email</th>
                                                        <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {(currentApproval.preview as MonitoringPreview).flagged_preview?.slice(0, 10).map((entity, idx) => (
                                                        <tr key={idx} className="border-t border-white/10">
                                                            <td className="px-4 py-3 text-sm text-white">{entity.name}</td>
                                                            <td className="px-4 py-3 text-sm text-white">{entity.email}</td>
                                                            <td className="px-4 py-3 text-sm">
                                                                <span className="px-2 py-1 text-xs font-medium rounded bg-yellow-400/20 text-yellow-400">
                                                                    Flagged
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}

                                {/* Analysis Template Details */}
                                {currentApproval.template === 'analysis' && (
                                    <div>
                                        <h3 className="mb-3 text-lg font-semibold text-white">Analysis Results</h3>
                                        <div className="p-4 border rounded-lg bg-white/5 border-white/10">
                                            <pre className="text-sm text-white whitespace-pre-wrap">
                                                {JSON.stringify((currentApproval.preview as AnalysisPreview).metrics, null, 2)}
                                            </pre>
                                        </div>
                                    </div>
                                )}

                                {/* Actions in Modal */}
                                <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                                    <Button onClick={() => setShowDetailsModal(false)} variant="outline" size="lg">
                                        Close
                                    </Button>
                                    <Button onClick={() => { setShowDetailsModal(false); handleApprove(); }} size="lg">
                                        <CheckCircle className="inline-block w-5 h-5 mr-2" />
                                        Approve & Execute
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </main>
    )
}