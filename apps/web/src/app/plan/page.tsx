'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { ChatMessage } from '../../components/ui/ChatMessage'
import { DebateViewer } from '../../components/ui/DebateViewer'
import { CheckCircle, Edit, X, Users, Clock, TrendingUp, AlertTriangle } from 'lucide-react'
import type { ApprovalGate, MatchingPreview, MonitoringPreview, AnalysisPreview, AgentName, DebateMessage } from '@trellis/types'
// MOCK: Import mock data - backend will replace with API calls
import { mockMatchingApproval, mockMonitoringApproval, mockAnalysisApproval } from '../../lib/mockData'

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
                
                // Fetch full approval details
                const approvalResponse = await fetch(`http://localhost:8000/approval/${data.approvalId}`)
                const approval = await approvalResponse.json()
                
                // Add approval message (debate message stays in history!)
                const approvalMessage: Message = {
                    id: (Date.now() + 3).toString(),
                    role: 'system',
                    content: `Debate complete! ${data.winner} won. Here's the preview:`,
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
                        metrics: data.preview
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
                    metrics: data.preview
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

    const handleApprove = () => {
        const approvalMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: 'Plan approved! Redirecting to the Approvals page...',
        }
        setMessages((prev) => [...prev, approvalMessage])
        setCurrentApproval(null)
        
        setTimeout(() => {
            router.push('/approvals')
        }, 1000)
    }

    const handleRevise = () => {
        const reviseMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: 'What would you like to change about the plan? Describe your adjustments.',
        }
        setMessages((prev) => [...prev, reviseMessage])
        setCurrentApproval(null)
    }

    const handleCancel = () => {
        const cancelMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: 'Plan cancelled. Feel free to start a new goal whenever you\'re ready.',
        }
        setMessages((prev) => [...prev, cancelMessage])
        setCurrentApproval(null)
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
            <div className="flex flex-col flex-1 w-full max-w-7xl mx-auto">
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
                                            {/* Your existing approval preview code stays the same */}
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
            </div>
        </main>
    )
}