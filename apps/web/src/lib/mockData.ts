// mockData.ts
// Mock data for the orchestrator ui 

import type {
    ApprovalGate,
    MatchingPreview,
    MonitoringPreview,
    AnalysisPreview,
    WorkflowResult
} from '@trellis/types'

export const mockMatchingApproval: ApprovalGate = {
    id: 'approval-1',
    template: 'matching',
    status: 'pending',
    createdAt: new Date().toISOString(),
    params: {
        sourceFile: 'volunteers.csv',
        targetFile: 'roles.csv',
        matchStrategy: 'capacity_balanced',
        notifications: [
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
                matchScore: 0.95,
                matchReason: 'Available Sundays, interests match'
            },
            {
                sourceId: '2',
                sourceName: 'Bob Smith',
                targetId: 'r2',
                targetName: 'Youth Leader',
                matchScore: 0.88,
                matchReason: 'Experience with youth ministry'
            },
            // Add 36 more...
        ],
        unmatched: [
            { id: '3', name: 'Carol White', reason: 'No Sunday availability' }
        ],
        capacityWarnings: ['Youth Leader at capacity (3/3)']
    } as MatchingPreview,
    metrics: {
        fillRate: 0.90,
        totalAssigned: 38,
        totalVolunteers: 42,
        rolesStaffed: 10
    }
}

export const mockMonitoringApproval: ApprovalGate = {
    id: 'approval-2',
    template: 'monitoring',
    status: 'pending',
    createdAt: new Date().toISOString(),
    params: {
        sourceFile: 'visitors.csv',
        filterRules: { daysSince: 14, noContact: true }
    },
    preview: {
        flaggedItems: [
            { id: '1', name: 'David Lee', lastContact: null, daysSince: 18, phone: '555-0101' },
            { id: '2', name: 'Emma Davis', lastContact: null, daysSince: 16, phone: '555-0102' },
            // Add 5 more...
        ],
        alertRecipients: ['pastor@church.org'],
        condition: 'Visited >14 days ago with no follow-up contact'
    } as MonitoringPreview,
    metrics: {
        flaggedCount: 7,
        avgDaysSince: 17,
        totalVisitors: 30
    }
}

export const mockAnalysisApproval: ApprovalGate = {
    id: 'approval-3',
    template: 'analysis',
    status: 'pending',
    createdAt: new Date().toISOString(),
    params: {
        sourceFile: 'gifts.csv',
        targetFile: 'initiatives.csv'
    },
    preview: {
        dimensions: [
            { name: 'Building Fund', current: 45000, goal: 100000, progress: 0.45, trend: 'up' },
            { name: 'Missions', current: 23000, goal: 50000, progress: 0.46, trend: 'up' },
            { name: 'Youth Ministry', current: 8500, goal: 15000, progress: 0.57, trend: 'stable' },
            { name: 'Community Outreach', current: 12000, goal: 20000, progress: 0.60, trend: 'up' },
            { name: 'General Fund', current: 67000, goal: 80000, progress: 0.84, trend: 'up' },
        ],
        lapsedItems: [
            { id: '1', name: 'Frank Wilson', lastDate: '2024-04-15', daysSince: 95, lifetimeTotal: 5400 },
            { id: '2', name: 'Grace Martinez', lastDate: '2024-05-01', daysSince: 78, lifetimeTotal: 3200 },
            // Add 21 more...
        ],
        totalAnalyzed: 200
    } as AnalysisPreview,
    metrics: {
        totalRaised: 155500,
        donorCount: 87,
        lapsedCount: 23,
        avgGift: 777
    }
}

export const mockMatchingResult: WorkflowResult = {
    id: 'result-1',
    template: 'matching',
    status: 'completed',
    completedAt: new Date().toISOString(),
    summary: 'Successfully assigned 38 volunteers to 10 roles',
    metrics: {
        assigned: 38,
        fillRate: '90%',
        messagesSent: 48,
        rolesStaffed: 10
    },
    actions: [
        { type: 'assignment', count: 38, description: 'Volunteer assignments created' },
        { type: 'notification', count: 38, description: 'SMS sent to volunteers' },
        { type: 'notification', count: 10, description: 'Email sent to role leaders' }
    ]
}