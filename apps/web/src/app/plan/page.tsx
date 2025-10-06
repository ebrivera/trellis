'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { ChatMessage } from '../../components/ui/ChatMessage'
import { CheckCircle, Edit, X, Users, Clock, TrendingUp, AlertTriangle } from 'lucide-react'
import type { ApprovalGate, MatchingPreview, MonitoringPreview, AnalysisPreview } from '@trellis/types'
// MOCK: Import mock data - backend will replace with API calls
import { mockMatchingApproval, mockMonitoringApproval, mockAnalysisApproval } from '../../lib/mockData'

type Message = {
    id: string
    role: 'user' | 'system'
    content: string
    approvalPreview?: ApprovalGate // Changed from planPreview to approvalPreview
    showActions?: boolean
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
    const [currentApproval, setCurrentApproval] = useState<ApprovalGate | null>(null) // Changed from currentPlan
    const [csvUrls, setCsvUrls] = useState<Record<string, string>>({})
    const [showCsvInput, setShowCsvInput] = useState(false)
    const [csvFiles, setCsvFiles] = useState<Record<string, File>>({})
    const [dataSource, setDataSource] = useState<'url' | 'file'>('url')
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = () => {
        if (!input.trim() || isProcessing) return

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
        }

        setMessages((prev) => [...prev, userMessage])
        setInput('')
        setIsProcessing(true)

        // MOCK: Simulate AI template classification
        // TODO: Backend will replace with POST /orchestrate API call
        // Real call: const response = await createWorkflow(input, csvUrls)
        setTimeout(() => {
            // Simple keyword detection to classify template
            // In production, LangGraph does this classification
            const requestLower = input.toLowerCase()
            let approval: ApprovalGate
            let templateName: string

            if (requestLower.includes('match') || requestLower.includes('assign') || requestLower.includes('volunteer') || requestLower.includes('pair')) {
                approval = mockMatchingApproval
                templateName = 'matching'
            } else if (requestLower.includes('track') || requestLower.includes('monitor') || requestLower.includes('flag') || requestLower.includes('visitor') || requestLower.includes('follow')) {
                approval = mockMonitoringApproval
                templateName = 'monitoring'
            } else if (requestLower.includes('trend') || requestLower.includes('analyz') || requestLower.includes('giving') || requestLower.includes('donor') || requestLower.includes('metric')) {
                approval = mockAnalysisApproval
                templateName = 'analysis'
            } else {
                // Default to matching if unclear
                approval = mockMatchingApproval
                templateName = 'matching'
            }

            const systemMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'system',
                content: `I've analyzed your request and classified it as a **${templateName}** workflow. Here's the preview:`,
                approvalPreview: approval,
                showActions: true,
            }

            setMessages((prev) => [...prev, systemMessage])
            setCurrentApproval(approval)
            setIsProcessing(false)
        }, 1500)
    }

    const handleApprove = () => {
        // MOCK: In production, this would create the approval in the backend
        // TODO: Backend will replace with POST /approval API call
        // Real call: await approveWorkflow(currentApproval.id)
        
        const approvalMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: 'Plan approved! Redirecting to the Approvals page...',
        }
        setMessages((prev) => [...prev, approvalMessage])
        setCurrentApproval(null)
        
        // Navigate to approvals page after brief delay
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
            <div className="flex flex-col flex-1 w-full max-w-5xl mx-auto">
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
            
            {/* // Add after templates section, before chat messages: */}
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
                <div className="flex-1 mb-6 space-y-4 overflow-y-auto max-h-[500px]">
                    {messages.map((message) => (
                    <div key={message.id} className="space-y-4">
                        <ChatMessage role={message.role}>
                            {message.content}
                        </ChatMessage>

                        {message.approvalPreview && (
                        <div className="ml-0 md:ml-12">
                            <Card padding="lg" className="space-y-4 bg-white/5">
                                {/* Header with template badge */}
                                <div className="flex items-center justify-between gap-3">
                                    <div className="flex items-center gap-3">
                                        <Badge variant={message.approvalPreview.template === 'matching' ? 'info' : message.approvalPreview.template === 'monitoring' ? 'default' : 'success'}>
                                            {message.approvalPreview.template.charAt(0).toUpperCase() + message.approvalPreview.template.slice(1)} Template
                                        </Badge>
                                        <h3 className="text-xl font-bold text-white">
                                            {message.approvalPreview.template === 'matching' && `Match ${(message.approvalPreview.preview as MatchingPreview).assignments.length} assignments`}
                                            {message.approvalPreview.template === 'monitoring' && `Monitor ${(message.approvalPreview.preview as MonitoringPreview).flaggedItems.length} flagged items`}
                                            {message.approvalPreview.template === 'analysis' && `Analyze ${(message.approvalPreview.preview as AnalysisPreview).dimensions.length} dimensions`}
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
                                                {message.approvalPreview.template === 'matching' && `${(message.approvalPreview.preview as MatchingPreview).assignments.length} proposed assignments from ${message.approvalPreview.params.sourceFile}${message.approvalPreview.params.targetFile ? ` to ${message.approvalPreview.params.targetFile}` : ''}`}
                                                {message.approvalPreview.template === 'monitoring' && `${(message.approvalPreview.preview as MonitoringPreview).flaggedItems.length} items flagged: ${(message.approvalPreview.preview as MonitoringPreview).condition}`}
                                                {message.approvalPreview.template === 'analysis' && `Analysis of ${(message.approvalPreview.preview as AnalysisPreview).totalAnalyzed} records with ${(message.approvalPreview.preview as AnalysisPreview).lapsedItems.length} items requiring attention`}
                                            </p>
                                            {/* Show key metrics */}
                                            <div className="flex flex-wrap gap-3 text-xs">
                                                {Object.entries(message.approvalPreview.metrics).slice(0, 3).map(([key, value]) => (
                                                    <div key={key} className="flex items-center gap-1">
                                                        <span className="text-white/50">{key}:</span>
                                                        <span className="font-semibold text-white">{value}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Warnings/Unmatched items */}
                                    {message.approvalPreview.template === 'matching' && (message.approvalPreview.preview as MatchingPreview).unmatched.length > 0 && (
                                        <div className="flex items-start gap-2 p-2 mt-2 border rounded bg-yellow-400/10 border-yellow-400/20">
                                            <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                                            <p className="text-xs text-yellow-300">
                                                {(message.approvalPreview.preview as MatchingPreview).unmatched.length} items couldn&apos;t be matched
                                            </p>
                                        </div>
                                    )}
                                </div>

                                 {message.showActions && (
                                     <div className="flex flex-wrap gap-3 pt-4">
                                         <Button onClick={handleApprove} size="lg">
                                             <CheckCircle className="inline-block w-5 h-5 mr-2" />
                                             Approve & Continue
                                         </Button>
                                         <Button onClick={handleRevise} variant="outline" size="lg">
                                             <Edit className="inline-block w-5 h-5 mr-2" />
                                             Revise Plan
                                         </Button>
                                         <Button onClick={handleCancel} variant="ghost" size="lg">
                                             <X className="inline-block w-5 h-5 mr-2" />
                                             Cancel
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
            </div>
        </main>
    )
}

