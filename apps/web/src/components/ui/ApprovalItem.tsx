import { Card } from './Card'
import { Button } from './Button'
import { Badge } from './Badge'
import { CheckCircle, X, Eye, AlertTriangle, Lock, Info } from 'lucide-react'

export interface ApprovalItemData {
    id: string
    title: string
    type: 'group-assignment' | 'message-draft' | 'event-update'
    summary: string
    riskFlags?: Array<{
        type: 'warning' | 'danger' | 'info'
        message: string
    }>
    details?: {
        description: string
        content?: string
        affectedCount?: number
        metadata?: Record<string, string>
    }
}

interface ApprovalItemProps {
    item: ApprovalItemData
    onApprove: (id: string) => void
    onReject: (id: string) => void
    onViewDetails: (id: string) => void
}

const typeLabels = {
    'group-assignment': 'Group Assignment',
    'message-draft': 'Message Draft',
    'event-update': 'Event Update',
}

const typeVariants = {
    'group-assignment': 'info' as const,
    'message-draft': 'default' as const,
    'event-update': 'success' as const,
}

export function ApprovalItem({
    item,
    onApprove,
    onReject,
    onViewDetails,
}: ApprovalItemProps) {
    return (
        <Card padding="lg" className="transition-all hover:bg-white/15">
            <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-2">
                            <Badge variant={typeVariants[item.type]}>
                                {typeLabels[item.type]}
                            </Badge>
                            {item.details?.affectedCount && (
                                <span className="text-sm text-white/60">
                                {item.details.affectedCount} affected
                                </span>
                            )}
                        </div>
                        <h3 className="text-xl font-semibold text-white">{item.title}</h3>
                    </div>
                </div>

                {/* Summary */}
                <p className="text-white/80">{item.summary}</p>

                {/* Risk Flags */}
                {item.riskFlags && item.riskFlags.length > 0 && (
                <div className="space-y-2">
                    {item.riskFlags.map((flag, idx) => (
                    <div
                        key={idx}
                        className={`flex items-start gap-2 p-3 rounded-lg ${
                        flag.type === 'warning'
                            ? 'bg-yellow-400/10 border border-yellow-400/20'
                            : flag.type === 'danger'
                            ? 'bg-red-400/10 border border-red-400/20'
                            : 'bg-blue-400/10 border border-blue-400/20'
                        }`}
                    >
                <div className="shrink-0">
                  {flag.type === 'warning' ? (
                    <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  ) : flag.type === 'danger' ? (
                    <Lock className="w-5 h-5 text-red-400" />
                  ) : (
                    <Info className="w-5 h-5 text-blue-400" />
                  )}
                </div>
                        <p
                        className={`text-sm ${
                            flag.type === 'warning'
                            ? 'text-yellow-300'
                            : flag.type === 'danger'
                            ? 'text-red-300'
                            : 'text-blue-300'
                        }`}
                        >
                        {flag.message}
                        </p>
                    </div>
                    ))}
                </div>
                )}

        {/* Actions */}
        <div className="flex flex-wrap gap-3 pt-2">
          <Button onClick={() => onApprove(item.id)} size="md">
            <CheckCircle className="inline-block w-4 h-4 mr-2" />
            Approve
          </Button>
          <Button onClick={() => onReject(item.id)} variant="outline" size="md">
            <X className="inline-block w-4 h-4 mr-2" />
            Reject
          </Button>
          <Button onClick={() => onViewDetails(item.id)} variant="ghost" size="md">
            <Eye className="inline-block w-4 h-4 mr-2" />
            View Details
          </Button>
        </div>
            </div>
        </Card>
    )
}

export default ApprovalItem

