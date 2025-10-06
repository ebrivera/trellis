import type { ApprovalGate, WorkflowResult } from '@trellis/types'
import { mockMatchingApproval, mockMatchingResult } from './mockData'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function createWorkflow(request: string, csvUrls: Record<string, string>) {
    // TODO: Replace with real API
    await new Promise(resolve => setTimeout(resolve, 1500))
    return { approvalId: 'approval-1' }
    
    // Real implementation:
    // const res = await fetch(`${API_BASE}/orchestrate`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ request, csv_urls: csvUrls })
    // })
    // return res.json()
}

export async function getApproval(id: string): Promise<ApprovalGate> {
    // TODO: Replace with real API
    await new Promise(resolve => setTimeout(resolve, 300))
    return mockMatchingApproval
    
    // Real implementation:
    // const res = await fetch(`${API_BASE}/approval/${id}`)
    // return res.json()
}

export async function approveWorkflow(id: string): Promise<{ resultId: string }> {
    // TODO: Replace with real API
    await new Promise(resolve => setTimeout(resolve, 1000))
    return { resultId: 'result-1' }
    
    // Real implementation:
    // const res = await fetch(`${API_BASE}/approval/${id}/approve`, {
    //   method: 'POST'
    // })
    // return res.json()
}

export async function rejectWorkflow(id: string): Promise<void> {
    // TODO: Replace with real API
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Real implementation:
    // await fetch(`${API_BASE}/approval/${id}/reject`, { method: 'POST' })
}

export async function getResult(id: string): Promise<WorkflowResult> {
    // TODO: Replace with real API
    await new Promise(resolve => setTimeout(resolve, 300))
    return mockMatchingResult
    
    // Real implementation:
    // const res = await fetch(`${API_BASE}/result/${id}`)
    // return res.json()
}