// orchestrator.ts
// Type definitions for the simplified 3-template orchestration system
// Design philosophy: Fixed templates instead of dynamic schema generation for faster development

/**
 * The 3 hardcoded workflow templates that cover most church automation use cases:
 * - matching: Assign entities to targets with constraints (volunteers→roles, mentors→mentees)
 * - monitoring: Detect conditions over time and alert (visitor follow-ups, lapsed donors)
 * - analysis: Aggregate data and recommend actions (giving trends, engagement metrics)
 */
export type TemplateType = 'matching' | 'monitoring' | 'analysis'

export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

/**
 * ApprovalGate represents a paused workflow awaiting human review
 * Key design: Every workflow stops before write operations (assignments, notifications)
 * This ensures humans always review AI decisions before they affect real people
 */
export interface ApprovalGate {
    id: string // Unique identifier for this approval gate
    template: TemplateType // Which of the 3 templates is being used
    status: ApprovalStatus // Current approval state
    createdAt: string // ISO timestamp for audit trail
    params: WorkflowParams // User-provided + AI-extracted parameters
    preview: MatchingPreview | MonitoringPreview | AnalysisPreview // Template-specific preview data
    metrics: Record<string, number> // High-level metrics for quick decision-making (e.g., fillRate: 0.90)
}

/**
 * WorkflowParams holds both user-provided data and AI-extracted parameters
 * Design: Keep fields optional so templates can share the same type
 * AI extracts these from natural language + CSV URLs
 */
export interface WorkflowParams {
    sourceFile: string // Primary data source (volunteers.csv, visitors.csv, gifts.csv)
    targetFile?: string // Optional target for matching template (roles.csv, initiatives.csv)
    filterRules?: Record<string, any> // Conditions like {daysSince: 14, noContact: true}
    matchStrategy?: 'capacity_balanced' | 'interest_overlap' | 'proximity' // How to pair source→target
    notifications?: NotificationTemplate[] // Messages to send after approval
}

/**
 * NotificationTemplate defines who gets messaged and how
 * Design: Template variables like {{targetName}} get filled at send time
 * Supports both SMS (Twilio) and email (Mailgun) in test mode
 */
export interface NotificationTemplate {
    to: 'source' | 'target' | 'admin' // Who receives: the matched entity, their match, or an admin
    channel: 'sms' | 'email' // Delivery method
    message: string // Template string with {{variable}} placeholders
}

/**
 * MatchingPreview: Shows proposed pairings before creating assignments
 * Use case: Volunteers→Roles, Mentors→Mentees, People→Groups
 * Design: User sees ALL assignments + problems (unmatched, over-capacity) in one view
 */
export interface MatchingPreview {
    assignments: MatchingAssignment[] // Successful pairings (e.g., 38 volunteers matched)
    unmatched: UnmatchedItem[] // Entities that couldn't be matched (e.g., 4 volunteers)
    capacityWarnings: string[] // Targets at/over capacity (e.g., "Youth Leader at capacity 3/3")
}

/**
 * MatchingAssignment: A single proposed pairing
 * matchScore helps user understand quality (0.0-1.0)
 * matchReason explains the AI's decision in human terms
 */
export interface MatchingAssignment {
    sourceId: string // ID from source CSV
    sourceName: string // Display name (e.g., "Alice Johnson")
    targetId: string // ID from target CSV
    targetName: string // Display name (e.g., "Sunday Greeter")
    matchScore: number // 0.0-1.0, higher is better match
    matchReason: string // Human-readable explanation (e.g., "Available Sundays, interests match")
}

/**
 * UnmatchedItem: Entity that couldn't be paired
 * Always include reason so user understands why (crucial for transparency)
 */
export interface UnmatchedItem {
    id: string
    name: string
    reason: string // e.g., "No Sunday availability", "All roles at capacity"
}

/**
 * MonitoringPreview: Shows items that match a time-based condition
 * Use case: Visitor follow-ups, lapsed donors, inactive volunteers
 * Design: Focus on "who needs attention" with clear time indicators
 */
export interface MonitoringPreview {
    flaggedItems: FlaggedItem[] // Items that matched the condition (e.g., 7 visitors)
    alertRecipients: string[] // Who gets notified (e.g., ["pastor@church.org"])
    condition: string // Human-readable filter (e.g., "Visited >14 days ago with no follow-up")
}

/**
 * FlaggedItem: A single entity that needs attention
 * daysSince is critical for urgency assessment
 * Contact info optional (depends on what's in CSV)
 */
export interface FlaggedItem {
    id: string
    name: string
    lastContact: string | null // ISO date or null if never contacted
    daysSince: number // Days since visit/donation/activity (for sorting by urgency)
    phone?: string // Optional contact info from CSV
    email?: string
}

/**
 * AnalysisPreview: Shows aggregated metrics and outliers
 * Use case: Giving trends by initiative, capacity analysis, engagement scores
 * Design: Dashboard-style with progress bars + list of items needing attention
 */
export interface AnalysisPreview {
    dimensions: AnalysisDimension[] // Grouped metrics (e.g., 5 initiatives with progress)
    lapsedItems: LapsedItem[] // Outliers needing attention (e.g., 23 lapsed donors)
    totalAnalyzed: number // Total records processed (for context)
}

/**
 * AnalysisDimension: A single metric group (initiative, ministry, etc.)
 * progress field enables progress bars in UI
 * trend helps user see direction without historical data
 */
export interface AnalysisDimension {
    name: string // Dimension name (e.g., "Building Fund")
    current: number // Current value (e.g., $45,000 raised)
    goal?: number // Optional target (e.g., $100,000)
    progress?: number // 0.0-1.0 for progress bar (current/goal)
    trend: 'up' | 'down' | 'stable' // Inferred from recent data
}

/**
 * LapsedItem: Entity that hasn't engaged recently
 * lifetimeTotal provides context for prioritization (high-value donors first)
 */
export interface LapsedItem {
    id: string
    name: string
    lastDate: string // ISO date of last activity
    daysSince: number // Days since last activity (for sorting)
    lifetimeTotal?: number // Optional lifetime value (e.g., $5,400 donated)
}

/**
 * WorkflowResult: Final outcome after approval + execution
 * Shown on /results/:id page after user approves
 * Design: Emphasize what actually happened (audit trail)
 */
export interface WorkflowResult {
    id: string
    template: TemplateType
    status: 'completed' | 'failed' // Whether execution succeeded
    completedAt: string // ISO timestamp for audit log
    summary: string // One-sentence outcome (e.g., "Successfully assigned 38 volunteers to 10 roles")
    metrics: Record<string, number | string> // Key stats (fillRate: "90%", assigned: 38)
    actions: ResultAction[] // List of concrete actions taken (for audit + transparency)
}

/**
 * ResultAction: A single action performed during workflow execution
 * Design: User sees exactly what happened (not just "workflow complete")
 * Critical for trust and debugging
 */
export interface ResultAction {
    type: 'assignment' | 'notification' | 'calculation' // Category of action
    count: number // How many (e.g., 38 assignments, 48 messages)
    description: string // Human-readable (e.g., "SMS sent to volunteers")
    details?: any // Optional detailed data (e.g., list of phone numbers for debugging)
}