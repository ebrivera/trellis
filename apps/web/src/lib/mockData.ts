// mockData.ts
// Mock data for testing the orchestrator UI without a backend
// Design goal: Realistic church data that demonstrates each template's value
// These examples are based on actual church use cases from the requirements doc

import type {
    ApprovalGate,
    MatchingPreview,
    MonitoringPreview,
    AnalysisPreview,
    WorkflowResult
} from '@trellis/types'

/**
 * mockMatchingApproval: Volunteer→Role assignment example
 * Demonstrates: High match rate (90%), capacity warnings, unmatched handling
 * Why this scenario: Most common church automation use case
 */
export const mockMatchingApproval: ApprovalGate = {
    id: 'approval-1',
    template: 'matching',
    status: 'pending',
    createdAt: new Date().toISOString(),
    params: {
        sourceFile: 'volunteers.csv', // Google Sheet with 50 volunteer records
        targetFile: 'roles.csv', // 10 roles needing volunteers
        matchStrategy: 'capacity_balanced', // Spread volunteers evenly across roles
        notifications: [
            // Dual notification: inform both volunteers and role leaders
            { to: 'source', channel: 'sms', message: 'You are assigned to {{targetName}}' },
            { to: 'target', channel: 'email', message: 'New volunteers: {{sourceNames}}' }
    ]
    },
    preview: {
        assignments: [
            {
                sourceId: '1',
                sourceName: 'Alice Johnson',
                targetId: 'r1',
                targetName: 'Sunday Greeter',
                matchScore: 0.95, // High score: perfect availability + interest match
                matchReason: 'Available Sundays, interests match'
            },
            {
                sourceId: '2',
                sourceName: 'Bob Smith',
                targetId: 'r2',
                targetName: 'Youth Leader',
                matchScore: 0.88, // Good score: has relevant experience
                matchReason: 'Experience with youth ministry'
            },
            // In real demo: would show 36 more assignments here
            // Kept short for mockData clarity
        ],
        unmatched: [
            // Critical: Show why some volunteers couldn't be placed
            { id: '3', name: 'Carol White', reason: 'No Sunday availability' }
        ],
        capacityWarnings: ['Youth Leader at capacity (3/3)'] // Alert user to at-capacity roles
    } as MatchingPreview,
    metrics: {
        fillRate: 0.90, // 90% of volunteers successfully placed
        totalAssigned: 38,
        totalVolunteers: 42, // 4 couldn't be matched
        rolesStaffed: 10 // All 10 roles filled
    }
}

/**
 * mockMonitoringApproval: Visitor follow-up tracking example
 * Demonstrates: Time-based filtering, urgency indicators, alert routing
 * Why this scenario: Churches struggle with systematic visitor follow-up
 * Key metric: 7/30 visitors need attention (23% lapse rate)
 */
export const mockMonitoringApproval: ApprovalGate = {
    id: 'approval-2',
    template: 'monitoring',
    status: 'pending',
    createdAt: new Date().toISOString(),
    params: {
        sourceFile: 'visitors.csv', // 30 first-time visitors over 2 months
        filterRules: { daysSince: 14, noContact: true } // AI-extracted condition
    },
    preview: {
        flaggedItems: [
            // Sorted by daysSince (most urgent first)
            { id: '1', name: 'David Lee', lastContact: null, daysSince: 18, phone: '555-0101' },
            { id: '2', name: 'Emma Davis', lastContact: null, daysSince: 16, phone: '555-0102' },
            // In real demo: 5 more flagged visitors
        ],
        alertRecipients: ['pastor@church.org'], // Who gets the alert
        condition: 'Visited >14 days ago with no follow-up contact' // Human-readable filter
    } as MonitoringPreview,
    metrics: {
        flaggedCount: 7, // How many need attention
        avgDaysSince: 17, // Average days without contact
        totalVisitors: 30 // Total in dataset for context
    }
}

/**
 * mockAnalysisApproval: Giving trends + lapsed donor identification
 * Demonstrates: Multi-dimension analysis, progress tracking, high-value outliers
 * Why this scenario: Churches need visibility into giving patterns
 * Design choice: Show 5 initiatives (not overwhelming) + prioritize high-lifetime donors
 */
export const mockAnalysisApproval: ApprovalGate = {
    id: 'approval-3',
    template: 'analysis',
    status: 'pending',
    createdAt: new Date().toISOString(),
    params: {
        sourceFile: 'gifts.csv', // 200 gift records over several months
        targetFile: 'initiatives.csv' // 5 active fundraising initiatives
    },
    preview: {
        dimensions: [
            // Sorted by progress (lowest first) to highlight initiatives needing attention
            { name: 'Building Fund', current: 45000, goal: 100000, progress: 0.45, trend: 'up' },
            { name: 'Missions', current: 23000, goal: 50000, progress: 0.46, trend: 'up' },
            { name: 'Youth Ministry', current: 8500, goal: 15000, progress: 0.57, trend: 'stable' },
            { name: 'Community Outreach', current: 12000, goal: 20000, progress: 0.60, trend: 'up' },
            { name: 'General Fund', current: 67000, goal: 80000, progress: 0.84, trend: 'up' }, // Closest to goal
        ],
        lapsedItems: [
            // Sorted by lifetimeTotal (high-value donors first for re-engagement priority)
            { id: '1', name: 'Frank Wilson', lastDate: '2024-04-15', daysSince: 95, lifetimeTotal: 5400 },
            { id: '2', name: 'Grace Martinez', lastDate: '2024-05-01', daysSince: 78, lifetimeTotal: 3200 },
            // In real demo: 21 more lapsed donors
        ],
        totalAnalyzed: 200 // Total gift records processed
    } as AnalysisPreview,
    metrics: {
        totalRaised: 155500, // Sum across all 5 initiatives
        donorCount: 87, // Unique donors
        lapsedCount: 23, // Donors who haven't given in >90 days
        avgGift: 777 // Average gift amount
    }
}

/**
 * mockMatchingResult: Completed workflow outcome for volunteer matching
 * Shown after user approves mockMatchingApproval and execution finishes
 * Design: Emphasize concrete actions taken (audit trail + transparency)
 * Note: 48 messages = 38 volunteers (SMS) + 10 leaders (email)
 */
export const mockMatchingResult: WorkflowResult = {
    id: 'result-1',
    template: 'matching',
    status: 'completed',
    completedAt: new Date().toISOString(),
    summary: 'Successfully assigned 38 volunteers to 10 roles', // One-sentence outcome
    metrics: {
        assigned: 38, // Number type for calculations
        fillRate: '90%', // String type for display
        messagesSent: 48, // Total notifications sent (38 SMS + 10 email)
        rolesStaffed: 10 // All roles filled
    },
    actions: [
        // Order matters: DB writes first, then notifications
        { type: 'assignment', count: 38, description: 'Volunteer assignments created' },
        { type: 'notification', count: 38, description: 'SMS sent to volunteers' },
        { type: 'notification', count: 10, description: 'Email sent to role leaders' }
    ]
}