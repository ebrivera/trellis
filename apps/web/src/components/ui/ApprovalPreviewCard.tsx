import { Card } from './Card'
import { Button } from './Button'
import { Badge } from './Badge'
import { CheckCircle, Eye, X, Users, Clock, TrendingUp, Save } from 'lucide-react'
import type { ApprovalGate } from '@trellis/types'

interface ApprovalPreviewCardProps {
    approval: ApprovalGate
    showActions: boolean
    isProcessing: boolean
    onApprove: () => void
    onSaveForLater: () => void
    onViewDetails: () => void
    onCancel: () => void
}

export function ApprovalPreviewCard({ 
    approval, 
    showActions, 
    isProcessing, 
    onApprove, 
    onSaveForLater, 
    onViewDetails, 
    onCancel 
}: ApprovalPreviewCardProps) {
    return (
        <Card padding="lg" className="space-y-4 bg-white/5">
            {/* Header */}
            <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                    <Badge variant={approval.template === 'matching' ? 'info' : approval.template === 'monitoring' ? 'default' : 'success'}>
                        {approval.template.charAt(0).toUpperCase() + approval.template.slice(1)} Template
                    </Badge>
                    <h3 className="text-xl font-bold text-white">
                        {approval.metrics['Proposed Assignments'] || 
                         approval.metrics['Flagged Count'] || 
                         approval.metrics['Total Analyzed'] || 0} items ready
                    </h3>
                </div>
                <span className="px-3 py-1 text-xs font-medium text-yellow-400 border rounded-full border-yellow-400/30 bg-yellow-400/10 shrink-0">
                    Requires Approval
                </span>
            </div>

            {/* Metrics Overview */}
            <div className="p-4 border rounded-lg bg-white/5 border-white/10">
                <div className="flex items-start gap-3">
                    {approval.template === 'matching' && <Users className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />}
                    {approval.template === 'monitoring' && <Clock className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />}
                    {approval.template === 'analysis' && <TrendingUp className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />}
                    <div className="flex-1">
                        <div className="grid grid-cols-2 gap-3 text-xs md:grid-cols-4">
                            {Object.entries(approval.metrics)
                                .slice(0, 4)
                                .map(([key, value]) => (
                                    <div key={key} className="flex flex-col gap-1">
                                        <span className="text-white/50">{key}</span>
                                        <span className="text-lg font-semibold text-white">{value}</span>
                                    </div>
                                ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions */}
            {showActions && (
                <div className="flex flex-wrap gap-3 pt-4">
                    <Button onClick={onApprove} size="lg" disabled={isProcessing}>
                        <CheckCircle className="inline-block w-5 h-5 mr-2" />
                        Approve & Execute
                    </Button>
                    <Button onClick={onSaveForLater} variant="outline" size="lg" disabled={isProcessing}>
                        <Save className="inline-block w-5 h-5 mr-2" />
                        Save for Later
                    </Button>
                    <Button onClick={onViewDetails} variant="outline" size="lg">
                        <Eye className="inline-block w-5 h-5 mr-2" />
                        View Details
                    </Button>
                    <Button onClick={onCancel} variant="ghost" size="lg" disabled={isProcessing}>
                        <X className="inline-block w-5 h-5 mr-2" />
                        Reject
                    </Button>
                </div>
            )}
        </Card>
    )
}
