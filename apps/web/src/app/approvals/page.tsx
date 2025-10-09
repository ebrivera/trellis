'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Badge } from '../../components/ui/Badge'
import type { ApprovalGate, MatchingPreview, MonitoringPreview, AnalysisPreview } from '@trellis/types'
import { Clock, PartyPopper, CheckCircle2, XCircle, Eye, AlertTriangle, TrendingUp } from 'lucide-react'

type Tab = 'pending' | 'saved' | 'approved' | 'rejected'

export default function ApprovalsPage() {
    const router = useRouter()
    const [activeTab, setActiveTab] = useState<Tab>('pending')
    const [pendingItems, setPendingItems] = useState<ApprovalGate[]>([])
    const [savedItems, setSavedItems] = useState<ApprovalGate[]>([])
    const [approvedItems, setApprovedItems] = useState<ApprovalGate[]>([])
    const [rejectedItems, setRejectedItems] = useState<ApprovalGate[]>([])
    const [selectedItem, setSelectedItem] = useState<ApprovalGate | null>(null)
    const [modalOpen, setModalOpen] = useState(false)
    const [loading, setLoading] = useState(true)

    // Fetch approvals from backend
    useEffect(() => {
        fetchApprovals()
    }, [])

    const fetchApprovals = async () => {
        try {
            setLoading(true)
            const response = await fetch('http://localhost:8000/approvals')

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const data = await response.json()

            if (!data.approvals || !Array.isArray(data.approvals)) {
                console.warn('No approvals found or invalid data structure')
                setPendingItems([])
                setSavedItems([])
                setApprovedItems([])
                setRejectedItems([])
                return
            }

            // Parse and categorize approvals
            const parsed = data.approvals.map((item: any) => {
                let previewData = {}
                let metrics = {}

                // Safely parse preview_data
                try {
                    if (item.preview_data) {
                        previewData = typeof item.preview_data === 'string'
                            ? JSON.parse(item.preview_data)
                            : item.preview_data
                    }
                } catch (e) {
                    console.error('Failed to parse preview_data:', e)
                }

                // Safely parse metrics
                try {
                    if (item.metrics) {
                        metrics = typeof item.metrics === 'string'
                            ? JSON.parse(item.metrics)
                            : item.metrics
                    }
                } catch (e) {
                    console.error('Failed to parse metrics:', e)
                }

                return {
                    id: item.id,
                    template: item.template_type,
                    status: item.status,
                    createdAt: item.created_at,
                    params: {}, // We'll populate this from extracted_params if needed
                    preview: previewData,
                    metrics: metrics || {}
                }
            })

            setPendingItems(parsed.filter((a: any) => a.status === 'pending'))
            setSavedItems(parsed.filter((a: any) => a.status === 'saved'))
            setApprovedItems(parsed.filter((a: any) => a.status === 'approved'))
            setRejectedItems(parsed.filter((a: any) => a.status === 'rejected'))
        } catch (error) {
            console.error('Failed to fetch approvals:', error)
            // Set empty arrays so the page doesn't crash
            setPendingItems([])
            setSavedItems([])
            setApprovedItems([])
            setRejectedItems([])
        } finally {
            setLoading(false)
        }
    }

    const handleApprove = async (id: string) => {
        try {
            await fetch(`http://localhost:8000/approval/${id}/decide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'approve' })
            })

            // Refresh approvals
            await fetchApprovals()

            // Close modal if open
            setModalOpen(false)

            // Navigate to approvals list (already there)
        } catch (error) {
            console.error('Failed to approve:', error)
        }
    }

    const handleReject = async (id: string) => {
        try {
            await fetch(`http://localhost:8000/approval/${id}/decide`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'reject' })
            })

            // Refresh approvals
            await fetchApprovals()

            // Close modal if open
            setModalOpen(false)
        } catch (error) {
            console.error('Failed to reject:', error)
        }
    }

    const handleViewDetails = (id: string) => {
        const allItems = [...pendingItems, ...savedItems, ...approvedItems, ...rejectedItems]
        const item = allItems.find((i) => i.id === id)
        if (item) {
            setSelectedItem(item)
            setModalOpen(true)
        }
    }

    const getCurrentItems = () => {
        switch (activeTab) {
            case 'pending':
                return pendingItems
            case 'saved':
                return savedItems
            case 'approved':
                return approvedItems
            case 'rejected':
                return rejectedItems
        }
    }

    const getApprovalTitle = (item: ApprovalGate) => {
        if (item.template === 'matching') {
            const preview = item.preview as any
            const count = preview.proposed_assignments || preview.assignments?.length || 0
            return `Match ${count} assignments`
        } else if (item.template === 'monitoring') {
            const preview = item.preview as any
            const count = preview.flagged_count || preview.flaggedItems?.length || 0
            return `Monitor ${count} flagged items`
        } else {
            const preview = item.preview as any
            const count = preview.total_analyzed || preview.totalAnalyzed || 0
            return `Analyze ${count} records`
        }
    }

    const getApprovalSummary = (item: ApprovalGate) => {
        if (item.template === 'matching') {
            const preview = item.preview as any
            const count = preview.proposed_assignments || preview.assignments?.length || 0
            return `${count} proposed assignments`
        } else if (item.template === 'monitoring') {
            const preview = item.preview as any
            const count = preview.flagged_count || preview.flaggedItems?.length || 0
            return `${count} items flagged based on time conditions`
        } else {
            const preview = item.preview as any
            const count = preview.total_analyzed || preview.totalAnalyzed || 0
            return `Analysis of ${count} records`
        }
    }

    const renderTemplatePreview = (item: ApprovalGate) => {
        if (item.template === 'matching') {
            const preview = item.preview as any
            const assignments = preview.assignments_preview || preview.assignments || []
            return (
                <div>
                    <h4 className="mb-2 text-sm font-semibold text-white/60">
                        Proposed Assignments ({assignments.length})
                    </h4>
                    <div className="overflow-y-auto border rounded-lg max-h-60 border-white/10">
                        <table className="w-full text-sm">
                            <thead className="sticky top-0 bg-black/80 backdrop-blur">
                                <tr className="text-left border-b text-white/60 border-white/10">
                                    <th className="p-2">Source</th>
                                    <th className="p-2">Target</th>
                                    <th className="p-2">Score</th>
                                </tr>
                            </thead>
                            <tbody className="text-white">
                                {assignments.slice(0, 10).map((a: any, i: number) => (
                                    <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                                        <td className="p-2">{a.source_name || a.sourceName}</td>
                                        <td className="p-2">{a.target_name || a.targetName}</td>
                                        <td className="p-2">
                                            <span className="text-green-400">
                                                {Math.round((a.match_score || a.matchScore || 0) * 100)}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {assignments.length > 10 && (
                            <p className="p-2 text-xs text-center text-white/50 bg-white/5">
                                +{assignments.length - 10} more assignments
                            </p>
                        )}
                    </div>
                    {preview.unmatched && preview.unmatched.length > 0 && (
                        <div className="p-3 mt-3 border rounded-lg bg-yellow-400/10 border-yellow-400/20">
                            <p className="text-sm text-yellow-300">
                                <AlertTriangle className="inline w-4 h-4 mr-1" />
                                {preview.unmatched.length} unmatched
                            </p>
                        </div>
                    )}
                </div>
            )
        }

        if (item.template === 'monitoring') {
            const preview = item.preview as any
            const flaggedItems = preview.flagged_preview || preview.flaggedItems || []
            return (
                <div>
                    <h4 className="mb-2 text-sm font-semibold text-white/60">
                        Flagged Items ({flaggedItems.length})
                    </h4>
                    <div className="space-y-2 overflow-y-auto max-h-60">
                        {flaggedItems.slice(0, 10).map((flagged: any, i: number) => (
                            <div key={i} className="p-3 border rounded-lg bg-white/5 border-white/10">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <span className="font-medium text-white">{flagged.name}</span>
                                        {flagged.email && (
                                            <p className="mt-1 text-sm text-white/60">{flagged.email}</p>
                                        )}
                                    </div>
                                    <span className="px-2 py-1 text-xs font-medium rounded bg-yellow-400/20 text-yellow-400">
                                        Flagged
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )
        }

        if (item.template === 'analysis') {
            const preview = item.preview as any
            return (
                <div>
                    <h4 className="mb-2 text-sm font-semibold text-white/60">Analysis Results</h4>
                    <div className="p-4 border rounded-lg bg-white/5 border-white/10">
                        <pre className="text-sm text-white whitespace-pre-wrap">
                            {JSON.stringify(preview.metrics || preview, null, 2)}
                        </pre>
                    </div>
                </div>
            )
        }

        return null
    }

    const currentItems = getCurrentItems()

    return (
        <main className="min-h-screen px-6 pt-32 pb-20">
            <div className="w-full max-w-5xl mx-auto">
                {/* Header */}
                <header className="mb-8">
                    <h1 className="mb-2 text-4xl font-bold text-white">Approvals</h1>
                    <p className="text-lg text-white/70">
                        Review and confirm Trellis&rsquo;s suggested actions before they go live.
                    </p>
          {pendingItems.length > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 mt-4 border rounded-lg bg-yellow-400/10 border-yellow-400/30 w-fit">
              <Clock className="w-6 h-6 text-yellow-400" />
              <p className="font-medium text-yellow-300">
                {pendingItems.length} {pendingItems.length === 1 ? 'action' : 'actions'} require
                your review
              </p>
            </div>
          )}
                </header>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
                <TabButton
                    active={activeTab === 'pending'}
                    onClick={() => setActiveTab('pending')}
                    count={pendingItems.length}
                >
                    Pending
                </TabButton>
                <TabButton
                    active={activeTab === 'saved'}
                    onClick={() => setActiveTab('saved')}
                    count={savedItems.length}
                >
                    Saved
                </TabButton>
                <TabButton
                    active={activeTab === 'approved'}
                    onClick={() => setActiveTab('approved')}
                    count={approvedItems.length}
                >
                    Approved
                </TabButton>
                <TabButton
                    active={activeTab === 'rejected'}
                    onClick={() => setActiveTab('rejected')}
                    count={rejectedItems.length}
                >
                    Rejected
                </TabButton>
            </div>

            {/* Items List */}
            <div className="space-y-4">
          {loading ? (
            <Card padding="lg" className="text-center">
              <div className="py-12">
                <div className="flex items-center justify-center gap-2">
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:0.2s]" />
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
                <p className="mt-4 text-white/70">Loading approvals...</p>
              </div>
            </Card>
          ) : currentItems.length === 0 ? (
            <Card padding="lg" className="text-center">
              <div className="py-12">
                <div className="flex justify-center mb-4">
                  {activeTab === 'pending' ? (
                    <PartyPopper className="w-16 h-16 text-green-400" />
                  ) : activeTab === 'saved' ? (
                    <Clock className="w-16 h-16 text-blue-400" />
                  ) : activeTab === 'approved' ? (
                    <CheckCircle2 className="w-16 h-16 text-green-400" />
                  ) : (
                    <XCircle className="w-16 h-16 text-red-400" />
                  )}
                </div>
                            <h3 className="mt-4 text-2xl font-bold text-white">
                                {activeTab === 'pending'
                                    ? "All caught up!"
                                    : activeTab === 'saved'
                                    ? 'No saved plans yet'
                                    : activeTab === 'approved'
                                    ? 'No approved items yet'
                                    : 'No rejected items'}
                            </h3>
                            <p className="mt-2 text-white/60">
                                {activeTab === 'pending'
                                    ? 'There are no pending approvals at the moment.'
                                    : activeTab === 'saved'
                                    ? 'Saved plans will appear here.'
                                    : activeTab === 'approved'
                                    ? 'Approved items will appear here.'
                                    : 'Rejected items will appear here.'}
                            </p>
                        </div>
                    </Card>
                ) : (
                    currentItems.map((item) => (
                        <Card key={item.id} padding="lg" className="transition-all hover:bg-white/15">
                            <div className="space-y-4">
                                {/* Header */}
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1">
                                        <div className="flex flex-wrap items-center gap-2 mb-2">
                                            <Badge variant={item.template === 'matching' ? 'info' : item.template === 'monitoring' ? 'default' : 'success'}>
                                                {item.template.charAt(0).toUpperCase() + item.template.slice(1)}
                                            </Badge>
                                            <span className="text-sm text-white/60">
                                                {new Date(item.createdAt).toLocaleString()}
                                            </span>
                                        </div>
                                        <h3 className="text-xl font-semibold text-white">
                                            {getApprovalTitle(item)}
                                        </h3>
                                    </div>
                                </div>

                                {/* Summary */}
                                <p className="text-white/80">{getApprovalSummary(item)}</p>

                                {/* Metrics */}
                                <div className="flex flex-wrap gap-4">
                                    {Object.entries(item.metrics).slice(0, 4).map(([key, value]) => (
                                        <div key={key} className="flex items-center gap-2">
                                            <TrendingUp className="w-4 h-4 text-blue-400" />
                                            <span className="text-sm text-white/60">{key}:</span>
                                            <span className="text-sm font-semibold text-white">
                                                {typeof value === 'object' && value !== null
                                                    ? JSON.stringify(value)
                                                    : String(value)}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Actions */}
                                {(activeTab === 'pending' || activeTab === 'saved') && (
                                    <div className="flex flex-wrap gap-3 pt-2">
                                        <Button onClick={() => handleApprove(item.id)} size="md">
                                            <CheckCircle2 className="inline-block w-4 h-4 mr-2" />
                                            Approve
                                        </Button>
                                        <Button onClick={() => handleReject(item.id)} variant="outline" size="md">
                                            <XCircle className="inline-block w-4 h-4 mr-2" />
                                            Reject
                                        </Button>
                                        <Button onClick={() => handleViewDetails(item.id)} variant="ghost" size="md">
                                            <Eye className="inline-block w-4 h-4 mr-2" />
                                            View Details
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </Card>
                    ))
                )}
            </div>

            {/* Details Modal */}
            <Modal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            title={selectedItem ? getApprovalTitle(selectedItem) : ''}
            >
            {selectedItem && (
                <div className="space-y-6">
                {/* Summary */}
                <div>
                    <h4 className="mb-2 text-sm font-semibold text-white/60">Overview</h4>
                    <p className="text-white">{getApprovalSummary(selectedItem)}</p>
                </div>

                {/* Template-specific preview */}
                {renderTemplatePreview(selectedItem)}

                {/* Metrics */}
                <div>
                    <h4 className="mb-2 text-sm font-semibold text-white/60">Metrics</h4>
                    <div className="grid grid-cols-2 gap-4">
                        {Object.entries(selectedItem.metrics).map(([key, value]) => (
                        <div key={key} className="p-3 rounded-lg bg-white/5">
                            <p className="mb-1 text-sm capitalize text-white/60">
                                {key.replace(/([A-Z])/g, ' $1').trim()}
                            </p>
                            <p className="text-lg font-semibold text-white">
                                {typeof value === 'object' && value !== null
                                    ? JSON.stringify(value, null, 2)
                                    : String(value)}
                            </p>
                        </div>
                        ))}
                    </div>
                </div>

              {/* Actions in Modal */}
              <div className="flex flex-wrap gap-3 pt-4 border-t border-white/10">
                <Button
                  onClick={() => {
                    handleApprove(selectedItem.id)
                    setModalOpen(false)
                  }}
                  size="lg"
                >
                  <CheckCircle2 className="inline-block w-5 h-5 mr-2" />
                  Approve
                </Button>
                <Button
                  onClick={() => {
                    handleReject(selectedItem.id)
                    setModalOpen(false)
                  }}
                  variant="outline"
                  size="lg"
                >
                  <XCircle className="inline-block w-5 h-5 mr-2" />
                  Reject
                </Button>
                    <Button onClick={() => setModalOpen(false)} variant="ghost" size="lg">
                    Close
                    </Button>
                </div>
                </div>
            )}
            </Modal>
            </div>
        </main>
    )
}

function TabButton({
    active,
    onClick,
    children,
    count,
}: {
    active: boolean
    onClick: () => void
    children: React.ReactNode
    count?: number
}) {
    return (
        <button
            onClick={onClick}
            className={`px-6 py-3 rounded-full font-medium transition-all ${
                active
                ? 'bg-white text-black'
                : 'bg-white/5 text-white border border-white/20 hover:bg-white/10'
            }`}
        >
        {children}
        {count !== undefined && count > 0 && (
            <span
            className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                active ? 'bg-black/10' : 'bg-white/10'
            }`}
            >
                {count}
            </span>
        )}
        </button>
    )
}

