import { Card } from './Card'
import { Button } from './Button'
import { Badge } from './Badge'
import { CheckCircle, X } from 'lucide-react'
import type { ApprovalGate, MatchingPreview, MonitoringPreview, AnalysisPreview } from '@trellis/types'

interface ApprovalDetailsModalProps {
    isOpen: boolean
    onClose: () => void
    approval: ApprovalGate | null
    onApprove: () => void
    isProcessing: boolean
}

export function ApprovalDetailsModal({ isOpen, onClose, approval, onApprove, isProcessing }: ApprovalDetailsModalProps) {
    if (!isOpen || !approval) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={onClose}>
            <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-gray-900 to-black border border-white/20 rounded-2xl" onClick={(e) => e.stopPropagation()}>
                {/* Modal Header */}
                <div className="sticky top-0 z-10 flex items-center justify-between p-6 border-b bg-gray-900/95 backdrop-blur-sm border-white/10">
                    <div className="flex items-center gap-3">
                        <Badge variant={approval.template === 'matching' ? 'info' : approval.template === 'monitoring' ? 'default' : 'success'}>
                            {approval.template.charAt(0).toUpperCase() + approval.template.slice(1)}
                        </Badge>
                        <h2 className="text-2xl font-bold text-white">Plan Details</h2>
                    </div>
                    <button
                        onClick={onClose}
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
                            {Object.entries(approval.metrics).map(([key, value]) => (
                                <div key={key} className="p-4 border rounded-lg bg-white/5 border-white/10">
                                    <p className="mb-1 text-sm text-white/60">{key}</p>
                                    <p className="text-2xl font-bold text-white">{value}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Extracted Parameters */}
                    <div>
                        <h3 className="mb-3 text-lg font-semibold text-white">Extracted Parameters</h3>
                        <div className="p-4 border rounded-lg bg-white/5 border-white/10">
                            <pre className="overflow-x-auto text-sm text-white whitespace-pre-wrap">
                                {JSON.stringify(approval.params, null, 2)}
                            </pre>
                        </div>
                    </div>

                    {/* Matching: Assignments Preview */}
                    {approval.template === 'matching' && (approval.preview as MatchingPreview).assignments_preview && (
                        <div>
                            <h3 className="mb-3 text-lg font-semibold text-white">Proposed Assignments (Preview)</h3>
                            <div className="overflow-hidden border rounded-lg border-white/10">
                                <table className="w-full">
                                    <thead className="bg-white/5">
                                        <tr>
                                            <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Source</th>
                                            <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Target</th>
                                            <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Score</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(approval.preview as MatchingPreview).assignments_preview.slice(0, 10).map((assignment, idx) => (
                                            <tr key={idx} className="border-t border-white/10">
                                                <td className="px-4 py-3 text-sm text-white">{assignment.sourceName}</td>
                                                <td className="px-4 py-3 text-sm text-white">{assignment.targetName}</td>
                                                <td className="px-4 py-3 text-sm">
                                                    <span className="px-2 py-1 text-xs font-medium rounded bg-blue-400/20 text-blue-400">
                                                        {Math.round((assignment.matchScore || 0) * 100)}%
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            {(approval.preview as MatchingPreview).assignments_preview.length > 10 && (
                                <p className="mt-2 text-sm text-white/50">
                                    Showing 10 of {(approval.preview as MatchingPreview).assignments_preview.length} assignments
                                </p>
                            )}
                        </div>
                    )}

                    {/* Monitoring: Flagged Items */}
                    {approval.template === 'monitoring' && (approval.preview as MonitoringPreview).flagged_preview && (
                        <div>
                            <h3 className="mb-3 text-lg font-semibold text-white">Flagged Entities</h3>
                            <div className="overflow-hidden border rounded-lg border-white/10">
                                <table className="w-full">
                                    <thead className="bg-white/5">
                                        <tr>
                                            <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Name</th>
                                            <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Email</th>
                                            <th className="px-4 py-3 text-sm font-medium text-left text-white/70">Days Since</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(approval.preview as MonitoringPreview).flagged_preview.slice(0, 10).map((entity, idx) => (
                                            <tr key={idx} className="border-t border-white/10">
                                                <td className="px-4 py-3 text-sm text-white">{entity.name}</td>
                                                <td className="px-4 py-3 text-sm text-white">{entity.email}</td>
                                                <td className="px-4 py-3 text-sm">
                                                    <span className="px-2 py-1 text-xs font-medium rounded bg-yellow-400/20 text-yellow-400">
                                                        {entity.daysSince} days
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Analysis: Metrics */}
                    {approval.template === 'analysis' && (
                        <div>
                            <h3 className="mb-3 text-lg font-semibold text-white">Analysis Results</h3>
                            <div className="p-4 border rounded-lg bg-white/5 border-white/10">
                                <pre className="text-sm text-white whitespace-pre-wrap">
                                    {JSON.stringify((approval.preview as AnalysisPreview).metrics, null, 2)}
                                </pre>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                        <Button onClick={onClose} variant="outline" size="lg">
                            Close
                        </Button>
                        <Button onClick={() => { onClose(); onApprove(); }} size="lg" disabled={isProcessing}>
                            <CheckCircle className="inline-block w-5 h-5 mr-2" />
                            Approve & Execute
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}
