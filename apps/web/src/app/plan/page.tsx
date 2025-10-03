'use client'

import { useState, useRef, useEffect } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { ChatMessage } from '../../components/ui/ChatMessage'
import { PlanCard } from '../../components/ui/PlanCard'
import { CheckCircle, Edit, X, FolderTree, Scale, Mail, MessageCircle } from 'lucide-react'
import { ReactNode } from 'react'

type Message = {
    id: string
    role: 'user' | 'system'
    content: string
    planPreview?: PlanPreview
    showActions?: boolean
}

type PlanPreview = {
    title: string
    items: Array<{
        icon: ReactNode
        title: string
        description: string
    }>
    requiresApproval: boolean
    approvalReason?: string
}

const DEMO_TEMPLATES = [
    'Template 1',
    'Template 2',
    'Template 3',
]

export default function GoalsPage() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'system',
            content: 'Hi! I\'m Trellis. Describe what you want to accomplish, and I\'ll help you create a structured plan with all the necessary steps.',
        },
    ])
    const [input, setInput] = useState('')
    const [isProcessing, setIsProcessing] = useState(false)
    const [currentPlan, setCurrentPlan] = useState<PlanPreview | null>(null)
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

    // Simulate processing
    setTimeout(() => {
        const plan: PlanPreview = {
            title: 'Fall Small Groups Plan',
            items: [
                {
                    icon: <FolderTree className="w-6 h-6 text-blue-400" />,
                    title: 'Create groups by ZIP code',
                    description: '8 groups will be formed based on geographic distribution',
                },
                {
                    icon: <Scale className="w-6 h-6 text-purple-400" />,
                    title: 'Balance group capacity',
                    description: 'Members will be distributed evenly (20-30 per group)',
                },
                {
                    icon: <Mail className="w-6 h-6 text-green-400" />,
                    title: 'Draft leader messages',
                    description: 'Personalized messages prepared for 8 group leaders',
                },
                {
                    icon: <MessageCircle className="w-6 h-6 text-pink-400" />,
                    title: 'Draft member messages',
                    description: 'Welcome messages prepared for 245 members',
                },
            ],
            requiresApproval: true,
            approvalReason: 'Mass messaging to 245+ people requires approval',
        }

        const systemMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'system',
            content: 'I\'ve created a plan for you. Here\'s what will happen:',
            planPreview: plan,
            showActions: true,
        }

        setMessages((prev) => [...prev, systemMessage])
        setCurrentPlan(plan)
        setIsProcessing(false)
    }, 1500)
    }

     const handleApprove = () => {
         const approvalMessage: Message = {
             id: Date.now().toString(),
             role: 'system',
             content: 'Plan approved! Your plan has been moved to the Approvals queue. You can review it on the Approvals page.',
         }
         setMessages((prev) => [...prev, approvalMessage])
         setCurrentPlan(null)
     }

    const handleRevise = () => {
        const reviseMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: 'What would you like to change about the plan? Describe your adjustments.',
        }
        setMessages((prev) => [...prev, reviseMessage])
        setCurrentPlan(null)
    }

    const handleCancel = () => {
        const cancelMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: 'Plan cancelled. Feel free to start a new goal whenever you\'re ready.',
        }
        setMessages((prev) => [...prev, cancelMessage])
        setCurrentPlan(null)
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

            {/* Chat Messages Container */}
            <Card className="flex flex-col flex-1 mb-6" padding="lg">
                <div className="flex-1 mb-6 space-y-4 overflow-y-auto max-h-[500px]">
                    {messages.map((message) => (
                    <div key={message.id} className="space-y-4">
                        <ChatMessage role={message.role}>
                            {message.content}
                        </ChatMessage>

                        {message.planPreview && (
                        <div className="ml-0 md:ml-12">
                            <Card padding="lg" className="space-y-4 bg-white/5">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-xl font-bold text-white">
                                        {message.planPreview.title}
                                    </h3>
                                    {message.planPreview.requiresApproval && (
                                    <span className="px-3 py-1 text-xs font-medium text-yellow-400 border rounded-full border-yellow-400/30 bg-yellow-400/10">
                                        Requires Approval
                                    </span>
                                    )}
                                </div>

                                {message.planPreview.approvalReason && (
                                    <p className="text-sm text-yellow-300/80">
                                        ⚠️ {message.planPreview.approvalReason}
                                    </p>
                                )}

                                <div className="space-y-3">
                                    {message.planPreview.items.map((item, idx) => (
                                    <PlanCard
                                        key={idx}
                                        icon={item.icon}
                                        title={item.title}
                                        description={item.description}
                                    />
                                    ))}
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

