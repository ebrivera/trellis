// orchestrator.ts
// Assumption of types for the orchestrator package based on the Google Docs Document. We can modify this as we go along.

export type TemplateType = 'matching' | 'monitoring' | 'analysis'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface ApprovalGate {
    id: string
    template: TemplateType
    status: ApprovalStatus
    createdAt: string
    params: WorkflowParams
    preview: MatchingPreview | MonitoringPreview | AnalysisPreview
    metrics: Record<string, number>
}

export interface WorkflowParams {
    sourceFile: string
    targetFile?: string
    filterRules?: Record<string, any>
    matchStrategy?: 'capacity_balanced' | 'interest_overlap' | 'proximity'
    notifications?: NotificationTemplate[]
}

export interface NotificationTemplate {
    to: 'source' | 'target' | 'admin'
    channel: 'sms' | 'email'
    message: string
}

// Matching template preview (volunteers → roles)
export interface MatchingPreview {
    assignments: MatchingAssignment[]
    unmatched: UnmatchedItem[]
    capacityWarnings: string[]
}

export interface MatchingAssignment {
    sourceId: string
    sourceName: string
    targetId: string
    targetName: string
    matchScore: number
    matchReason: string
}

export interface UnmatchedItem {
    id: string
    name: string
    reason: string
}

// Monitoring template preview (visitors follow-up)
export interface MonitoringPreview {
    flaggedItems: FlaggedItem[]
    alertRecipients: string[]
    condition: string
}

export interface FlaggedItem {
    id: string
    name: string
    lastContact: string | null
    daysSince: number
    phone?: string
    email?: string
}

// Analysis template preview (giving trends)
export interface AnalysisPreview {
    dimensions: AnalysisDimension[]
    lapsedItems: LapsedItem[]
    totalAnalyzed: number
}

export interface AnalysisDimension {
    name: string
    current: number
    goal?: number
    progress?: number
    trend: 'up' | 'down' | 'stable'
}

export interface LapsedItem {
    id: string
    name: string
    lastDate: string
    daysSince: number
    lifetimeTotal?: number
}

// Results page data
export interface WorkflowResult {
    id: string
    template: TemplateType
    status: 'completed' | 'failed'
    completedAt: string
    summary: string
    metrics: Record<string, number | string>
    actions: ResultAction[]
}

export interface ResultAction {
    type: 'assignment' | 'notification' | 'calculation'
    count: number
    description: string
    details?: any
}