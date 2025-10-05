'use client'

import { useState } from 'react'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Badge } from '../../components/ui/Badge'
import type { ApprovalGate, MatchingPreview, MonitoringPreview, AnalysisPreview } from '@trellis/types'
import { mockMatchingApproval, mockMonitoringApproval, mockAnalysisApproval } from '../../lib/mockData'
import { Clock, PartyPopper, CheckCircle2, XCircle, Eye, AlertTriangle, TrendingUp } from 'lucide-react'

type Tab = 'pending' | 'approved' | 'rejected'

const DEMO_APPROVALS: ApprovalGate[] = [
    mockMatchingApproval,
    mockMonitoringApproval,
    mockAnalysisApproval
]

export default function ApprovalsPage() {
    const [activeTab, setActiveTab] = useState<Tab>('pending')
    const [pendingItems, setPendingItems] = useState<ApprovalGate[]>(DEMO_APPROVALS)
    const [approvedItems, setApprovedItems] = useState<ApprovalGate[]>([])
    const [rejectedItems, setRejectedItems] = useState<ApprovalGate[]>([])
    const [selectedItem, setSelectedItem] = useState<ApprovalGate | null>(null)
    const [modalOpen, setModalOpen] = useState(false)

    const handleApprove = (id: string) => {
        const item = pendingItems.find((i) => i.id === id)
        if (item) {
            setPendingItems((prev) => prev.filter((i) => i.id !== id))
            setApprovedItems((prev) => [...prev, item])
        }
    }

    const handleReject = (id: string) => {
        const item = pendingItems.find((i) => i.id === id)
        if (item) {
            setPendingItems((prev) => prev.filter((i) => i.id !== id))
            setRejectedItems((prev) => [...prev, item])
        }
    }

    const handleViewDetails = (id: string) => {
        const item = pendingItems.find((i) => i.id === id)
        if (item) {
            setSelectedItem(item)
            setModalOpen(true)
        }
    }

    const getCurrentItems = () => {
        switch (activeTab) {
            case 'pending':
                return pendingItems
            case 'approved':
                return approvedItems
            case 'rejected':
                return rejectedItems
        }
    }

    const getApprovalTitle = (item: ApprovalGate) => {
        if (item.template === 'matching') {
            const preview = item.preview as MatchingPreview
            return `Match ${preview.assignments.length} assignments`
        } else if (item.template === 'monitoring') {
            const preview = item.preview as MonitoringPreview
            return `Monitor ${preview.flaggedItems.length} flagged items`
        } else {
            const preview = item.preview as AnalysisPreview
            return `Analyze ${preview.dimensions.length} dimensions`
        }
    }

    const getApprovalSummary = (item: ApprovalGate) => {
        if (item.template === 'matching') {
            const preview = item.preview as MatchingPreview
            return `${preview.assignments.length} proposed assignments from ${item.params.sourceFile}${item.params.targetFile ? ` to ${item.params.targetFile}` : ''}`
        } else if (item.template === 'monitoring') {
            const preview = item.preview as MonitoringPreview
            return `${preview.flaggedItems.length} items flagged: ${preview.condition}`
        } else {
            const preview = item.preview as AnalysisPreview
            return `Analysis of ${preview.totalAnalyzed} records with ${preview.lapsedItems.length} items requiring attention`
        }
    }

    const renderTemplatePreview = (item: ApprovalGate) => {
        if (item.template === 'matching') {
            const preview = item.preview as MatchingPreview
            return (
                <div>
                    <h4 className="mb-2 text-sm font-semibold text-white/60">
                        Proposed Assignments ({preview.assignments.length})
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
                                {preview.assignments.slice(0, 10).map((a, i) => (
                                    <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                                        <td className="p-2">{a.sourceName}</td>
                                        <td className="p-2">{a.targetName}</td>
                                        <td className="p-2">
                                            <span className="text-green-400">{Math.round(a.matchScore * 100)}%</span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {preview.assignments.length > 10 && (
                            <p className="p-2 text-xs text-center text-white/50 bg-white/5">
                                +{preview.assignments.length - 10} more assignments
                            </p>
                        )}
                    </div>
                    {preview.unmatched.length > 0 && (
                        <div className="p-3 mt-3 border rounded-lg bg-yellow-400/10 border-yellow-400/20">
                            <p className="text-sm text-yellow-300">
                                <AlertTriangle className="inline w-4 h-4 mr-1" />
                                {preview.unmatched.length} unmatched: {preview.unmatched.map(u => u.name).join(', ')}
                            </p>
                        </div>
                    )}
                </div>
            )
        }

        if (item.template === 'monitoring') {
            const preview = item.preview as MonitoringPreview
            return (
                <div>
                    <h4 className="mb-2 text-sm font-semibold text-white/60">
                        Flagged Items ({preview.flaggedItems.length})
                    </h4>
                    <div className="space-y-2 overflow-y-auto max-h-60">
                        {preview.flaggedItems.map((item, i) => (
                            <div key={i} className="p-3 border rounded-lg bg-white/5 border-white/10">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <span className="font-medium text-white">{item.name}</span>
                                        {item.phone && (
                                            <p className="mt-1 text-sm text-white/60">{item.phone}</p>
                                        )}
                                    </div>
                                    <span className="text-sm font-semibold text-yellow-400">
                                        {item.daysSince} days
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="p-3 mt-3 border rounded-lg bg-blue-400/10 border-blue-400/20">
                        <p className="text-sm text-blue-300">
                            Alert will be sent to: {preview.alertRecipients.join(', ')}
                        </p>
                    </div>
                </div>
            )
        }

        if (item.template === 'analysis') {
            const preview = item.preview as AnalysisPreview
            return (
                <div className="space-y-4">
                    <div>
                        <h4 className="mb-3 text-sm font-semibold text-white/60">
                            Analysis by Dimension
                        </h4>
                        <div className="space-y-3">
                            {preview.dimensions.map((dim, i) => (
                                <div key={i} className="p-3 border rounded-lg bg-white/5 border-white/10">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-medium text-white">{dim.name}</span>
                                        <span className="text-sm text-white/70">
                                            ${dim.current.toLocaleString()}
                                            {dim.goal && ` / $${dim.goal.toLocaleString()}`}
                                        </span>
                                    </div>
                                    {dim.progress !== undefined && (
                                        <div className="w-full h-2 overflow-hidden rounded-full bg-white/10">
                                            <div
                                                className="h-full transition-all bg-green-400"
                                                style={{ width: `${dim.progress * 100}%` }}
                                            />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div>
                        <h4 className="mb-2 text-sm font-semibold text-white/60">
                            Lapsed Items ({preview.lapsedItems.length})
                        </h4>
                        <div className="p-3 border rounded-lg bg-red-400/10 border-red-400/20">
                            <p className="text-sm text-red-300">
                                {preview.lapsedItems.slice(0, 5).map(item => item.name).join(', ')}
                                {preview.lapsedItems.length > 5 && ` +${preview.lapsedItems.length - 5} more`}
                            </p>
                        </div>
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
          {currentItems.length === 0 ? (
            <Card padding="lg" className="text-center">
              <div className="py-12">
                <div className="flex justify-center mb-4">
                  {activeTab === 'pending' ? (
                    <PartyPopper className="w-16 h-16 text-green-400" />
                  ) : activeTab === 'approved' ? (
                    <CheckCircle2 className="w-16 h-16 text-green-400" />
                  ) : (
                    <XCircle className="w-16 h-16 text-red-400" />
                  )}
                </div>
                            <h3 className="mt-4 text-2xl font-bold text-white">
                                {activeTab === 'pending'
                                    ? "All caught up!"
                                    : activeTab === 'approved'
                                    ? 'No approved items yet'
                                    : 'No rejected items'}
                            </h3>
                            <p className="mt-2 text-white/60">
                                {activeTab === 'pending'
                                    ? 'There are no pending approvals at the moment.'
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
                                            <span className="text-sm font-semibold text-white">{value}</span>
                                        </div>
                                    ))}
                                </div>

                                {/* Actions */}
                                {activeTab === 'pending' && (
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
                            <p className="text-lg font-semibold text-white">{value}</p>
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

