# FRONTEND Schema

### This is meant to be a markdown file that will explain the codebase

```
(venv) MacBookPro:trellis ernestorivera$ tree -I "venv|__pycache__|.next|node_modules"
.
(venv) MacBookPro:trellis ernestorivera$ tree -I "venv|__pycache__|.next|node_modules|test_*"
.
├── README.md
├── apps
│   └── web
│       ├── next-env.d.ts -
│       ├── next.config.js
│       ├── package.json
│       ├── postcss.config.js
│       ├── src
│       │   ├── app
│       │   │   ├── approvals
│       │   │   │   └── page.tsx
│       │   │   ├── debate-test
│       │   │   │   └── page.tsx
│       │   │   ├── globals.css
│       │   │   ├── globals_.swp
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx
│       │   │   ├── plan
│       │   │   │   └── page.tsx
│       │   │   ├── profile
│       │   │   │   └── page.tsx
│       │   │   ├── results
│       │   │   │   └── [id]
│       │   │   │       └── page.tsx
│       │   │   └── settings
│       │   │       └── page.tsx
│       │   ├── components
│       │   │   ├── layout
│       │   │   │   ├── Background.tsx
│       │   │   │   ├── Navbar.tsx
│       │   │   │   └── ProfileDropdown.tsx
│       │   │   └── ui
│       │   │       ├── ApprovalItem.tsx
│       │   │       ├── Badge.tsx
│       │   │       ├── Button.tsx
│       │   │       ├── Card.tsx
│       │   │       ├── ChatMessage.tsx
│       │   │       ├── DebateViewer.tsx
│       │   │       ├── Modal.tsx
│       │   │       ├── PlanCard.tsx
│       │   │       └── index.ts
│       │   ├── fe_tree.md
│       │   └── lib
│       │       ├── api.ts
│       │       ├── mockData.ts
│       │       └── utils.ts
│       ├── tailwind.config.js
│       └── tsconfig.json
├── orchestrator
│   ├── CORE_FUNCTIONS.md
│   ├── clear_test_data.py
│   ├── prompts
│   │   ├── agent_personas
│   │   │   ├── human_flourishing.txt
│   │   │   ├── moderator.txt
│   │   │   ├── operations.txt
│   │   │   └── planner.txt
│   │   ├── classify_template.txt
│   │   ├── extract_params_analysis.txt
│   │   ├── extract_params_matching.txt
│   │   └── extract_params_monitoring.txt
│   ├── requirements.in
│   ├── requirements.txt
│   ├── src
│   │   ├── database.py
│   │   ├── functions
│   │   │   ├── calculate_metrics.py
│   │   │   ├── filter.py
│   │   │   ├── load_data.py
│   │   │   ├── match.py
│   │   │   └── send_notification.py
│   │   ├── graph.py
│   │   ├── graph_executor.py
│   │   ├── graph_streaming.py
│   │   ├── main.py
│   │   ├── nodes
│   │   │   ├── LEGACY_extractor.py
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py
│   │   │   └── debate
│   │   │       ├── __init__.py
│   │   │       ├── agent.py
│   │   │       ├── extract_params.py
│   │   │       ├── orchestrator.py
│   │   │       ├── tiebreaker.py
│   │   │       └── voting.py
│   │   ├── schemas.py
│   │   └── templates
│   │       ├── __init__.py
│   │       ├── analysis.py
│   │       ├── matching.py
│   │       └── monitoring.py
│   └── tests
├── package-lock.json
├── package.json
├── packages
│   ├── types
│   │   ├── dist
│   │   │   ├── index.d.ts
│   │   │   ├── index.d.ts.map
│   │   │   ├── index.js
│   │   │   ├── index.js.map
│   │   │   ├── orchestrator.d.ts
│   │   │   ├── orchestrator.d.ts.map
│   │   │   ├── orchestrator.js
│   │   │   └── orchestrator.js.map
│   │   ├── package.json
│   │   ├── src
│   │   │   ├── index.ts
│   │   │   └── orchestrator.ts
│   │   └── tsconfig.json
│   └── utils
│       ├── dist
│       │   ├── index.d.ts
│       │   ├── index.d.ts.map
│       │   ├── index.js
│       │   └── index.js.map
│       ├── package.json
│       ├── src
│       │   └── index.ts
│       └── tsconfig.json
├── supabase
│   ├── config.toml
│   ├── migrations
│   │   └── 20251006000001_initial_schema.sql
│   └── seed.sql
├── tsconfig.json
└── turbo.json

34 directories, 95 files
```

## apps/web/src/app/plan/page.tsx — Chat planner (debate embedded in chat)

**Consumes:** user prompt; optional CSV/Sheet URLs or CSV files; SSE `/orchestrate/stream`; REST `GET /approval/{id}`  
**Produces:** chat transcript where a **debate block** is a message (via `debateData`), followed by an approval preview card

**State:**

- Core: `messages`, `input`, `isProcessing`, `currentApproval`
- CSV: `csvUrls`, `csvFiles`, `dataSource`
- (Legacy) `debateMessages/currentRound/winner/voteTally` kept but primary render uses `messages[].debateData`

**Effects (SSE flow):**

- On **Send**: append user msg → add “Analyzing…” system msg → insert **debate placeholder** message `{ debateData:{ messages:{Planner,Operations,HumanFlourishing,Moderator:[]}, currentRound:1 } }`
- `classifier_complete` → remove “Analyzing…” message
- `round_1_proposal` / `round_2_rebuttal` / `round_3_vote` → _in-place update_ the debate message’s `debateData.messages[agent]` and `currentRound`
- `voting_complete` → set `debateData.winner` + `debateData.voteTally` on that message
- `preview_ready` → fetch `/approval/{approvalId}` and **append** a new system message with `approvalPreview` (debate message remains in history)

**UI blocks:**

- Header + Quick Templates; CSV/Sheets toggle (URL|file)
- Chat list: each message renders `ChatMessage`; if it has `debateData`, render `<DebateViewer {...debateData} />` **inside the list**; if it has `approvalPreview`, render approval card
- Input row; container widened (`max-w-7xl`), chat `max-h-[600px]`

**Actions:**

- **Send** → start SSE, stream into the embedded debate message, then append approval preview
- **Approve** → system note then `push('/approvals')`
- **Revise/Cancel** → add system prompt

**Contracts:**

- `Message.debateData`: `{ messages: Record<AgentName, DebateMessage[]>; currentRound:1|2|3; winner?:AgentName; voteTally?:Record<AgentName,number> }`
- `template`: `'matching'|'monitoring'|'analysis'`; `metrics` = entries from `preview` (first few shown)

## apps/web/src/app/plan/page.tsx — Chat planner with SSE debate → approval

**Consumes:** user prompt; optional CSV/Sheet URLs or CSV files; SSE `/orchestrate/stream`; REST `GET /approval/{id}`  
**Produces:** chat transcript, DebateViewer updates, template-specific approval card; redirect to `/approvals` on approve  
**State:** messages, input, isProcessing; csvUrls, csvFiles, dataSource; currentApproval; debateMessages, currentRound, winner, voteTally, showDebate  
**Effects:**

- SSE events: `classifier_complete`, `debate_start`, `round_1_proposal`, `round_2_rebuttal`, `round_3_vote`, `voting_complete`, `preview_ready`, `complete`, `error`
- Fetch on `preview_ready`: `/approval/{approvalId}`  
  **UI blocks:** header + quick templates; CSV/Sheets toggle (URL|file) for source/target; chat list with conditional Approval Card; input bar; DebateViewer  
  **Actions:** Send → start SSE & render preview; Approve → push `/approvals`; Revise/Cancel → append system prompt  
  **Contracts:**
- `template`: `'matching'|'monitoring'|'analysis'`
- `preview` fields used → matching: `proposed_assignments`, `unmatched?`; monitoring: `flaggedItems`, `condition`; analysis: `dimensions`, `totalAnalyzed`, `lapsedItems`
- `metrics`: derived from `preview` (first 3 shown)

## apps/web/src/app/results/[id]/page.tsx — Result detail view

**Consumes:** route param `id`; (mock) `mockMatchingResult`; future `GET /result/:id`  
**Produces:** completed workflow summary with status badge, metrics grid, actions list; nav actions

**State:** `result: WorkflowResult|null`, `loading: boolean`  
**Effects:** `useEffect` → mock fetch (timeout) → set `result` (replace with API call)

**UI blocks:**

- Header: title “Workflow Complete”, `result.summary`, success `Badge`, completedAt timestamp
- “Key Metrics”: cards for `Object.entries(result.metrics)`
- “Actions Completed”: list rendering `result.actions[]`
- Footer actions: **Export Report** (stub), **View Approvals** → `/approvals`, **Create Another Workflow** → `/plan`, Back to Dashboard → `/`

**Actions:**

- Back button → `router.push('/')`
- Export Report (no backend wired)
- View Approvals → `router.push('/approvals')`
- Create Another Workflow → `router.push('/plan')`

**Contracts (`WorkflowResult` fields used):**

- `summary: string`, `status: string`, `completedAt: ISO string`
- `metrics: Record<string, number|string>`
- `actions: Array<{ description: string; type: string; count: number }>`

## apps/web/src/app/page.tsx — Dashboard landing

**Consumes:** (none — static UI)  
**Produces:** overview dashboard with counts, recent activity, quick links

**State:** (none)  
**Effects:** client-side navigation via `<Link>` only

**UI blocks:**

- **Hero:** “Welcome back, Pastor John” + CTA → `/plan`
- **Overview cards:** Pending Approvals (→ `/approvals`), Recent Workflows progress bar, Task Scheduled stats, generic Statistics
- **Recent Activity feed:** list items with optional “Review” → `/approvals`
- **Quick Actions:** Import Data → `/settings`, Start New Goal → `/plan`, Review Approvals → `/approvals`, View Reports (stub)
- **This Month snapshot:** three `MetricItem` tiles (label/value/change)

**Actions:**

- Start New Goal → `/plan`
- Review Approvals → `/approvals`
- Import Data → `/settings`
- Backed “View Reports” button (no route wired)

## apps/web/src/components/ui/ApprovalItem.tsx — Single approval row/card

**Consumes:** `item: ApprovalItemData`; callbacks `onApprove(id)`, `onReject(id)`, `onViewDetails(id)`  
**Produces:** styled card with type badge, summary, optional risk flags, and action buttons

**State:** (none)  
**Effects:** (none)

**UI blocks:** header (Badge by `item.type`, optional `affectedCount`, title); summary; risk flags list (warning/danger/info with icon+color); actions (Approve / Reject / View Details)

**Actions:**

- Approve → `onApprove(item.id)`
- Reject → `onReject(item.id)`
- View Details → `onViewDetails(item.id)`

**Contracts:**

- `ApprovalItemData`:
  - `id: string`, `title: string`, `type: 'group-assignment'|'message-draft'|'event-update'`, `summary: string`
  - `riskFlags?: { type: 'warning'|'danger'|'info'; message: string }[]`
  - `details?: { description: string; content?: string; affectedCount?: number; metadata?: Record<string,string> }`
- Visual variants map: `group-assignment→info`, `message-draft→default`, `event-update→success`

## apps/web/src/components/ui/DebateViewer.tsx — 3-agent debate panel

**Consumes:**  
`messages: Record<AgentName, DebateMessage[]>`, `currentRound: 1|2|3`, `winner?: AgentName`, `voteTally?: Record<AgentName, number>`

**Produces:**  
3-column live view (Planner / Operations / HumanFlourishing) showing per-round messages, winner badge, vote counts, and round selector

**State:**  
`selectedRound (1|2|3)` (auto-advances to `currentRound`), `expandedAgent: AgentName|null` (toggle truncation)

**Effects:**  
(no network; local state only)

**UI blocks:**

- Agent card (emoji, color theme, description, 🏆 badge if `winner`)
- Message list for **selectedRound** (truncates >200 chars; “Show more/less”)
- Vote footer (round 3 only)
- Round selector buttons (1–3) with states: active / complete / available / disabled

**Actions:**

- Click round pill → set `selectedRound` (≤ `currentRound`)
- “Show more/less” → toggle `expandedAgent` per agent

**Contracts (types/fields used):**

- Agents displayed: `'Planner' | 'Operations' | 'HumanFlourishing'` (Moderator not shown)
- `DebateMessage`: `round: 1|2|3`, `messageType: string`, `content: string`
- `voteTally[agent]: number` (shown only when `selectedRound === 3` and >0)

## apps/web/src/lib/api.ts — Client-side mock API layer

**Consumes:** optional `NEXT_PUBLIC_API_URL` env; mock data (`mockMatchingApproval`, `mockMatchingResult`)  
**Produces:** simulated responses for orchestration/approval/result actions; placeholder for real backend routes

**Functions:**

- `createWorkflow(request, csvUrls)` → `{ approvalId }` (mock delay 1.5 s)  
  _→ real: `POST /orchestrate` with `{ request, csv_urls }`_
- `getApproval(id)` → `ApprovalGate` mock (delay 0.3 s)  
  _→ real: `GET /approval/{id}`_
- `approveWorkflow(id)` → `{ resultId }` mock (delay 1 s)  
  _→ real: `POST /approval/{id}/approve`_
- `rejectWorkflow(id)` → void (delay 0.5 s)  
  _→ real: `POST /approval/{id}/reject`_
- `getResult(id)` → `WorkflowResult` mock (delay 0.3 s)  
  _→ real: `GET /result/{id}`_

**Contracts:**

- `ApprovalGate` = structured pending approval (id, template, params, preview, metrics)
- `WorkflowResult` = completed workflow summary (status, metrics, actions)

**Role:** temporary mock API bridge for local testing; mirrors backend endpoints under `${API_BASE}`.

## apps/web/src/app/approvals/page.tsx — Approvals list + modal review

**Consumes:** mock `ApprovalGate[]` (matching/monitoring/analysis)  
**Produces:** tabbed lists (Pending/Approved/Rejected), per-item metrics, detail modal, approve→results nav

**State:** `activeTab`, `pendingItems`, `approvedItems`, `rejectedItems`, `selectedItem`, `modalOpen`  
**Effects:** client nav `router.push('/results/{id}')` on approve (mock id)

**UI blocks:**

- Header with pending count callout
- Tabs (Pending/Approved/Rejected)
- Item card: template badge, createdAt, title, summary, top metrics (≤4), actions (Approve/Reject/View Details)
- Modal: overview, template-specific preview (matching table w/ unmatched alert; monitoring flagged list + recipients; analysis dimensions + progress + lapsed), full metrics, actions

**Actions:**

- Approve (pending → approved, close modal, `push('/results/{timestamp}')`)
- Reject (pending → rejected)
- View Details (open modal)
- Tab switch

**Contracts:**

- `ApprovalGate.template ∈ { 'matching'|'monitoring'|'analysis' }`
- Title/Summary derived from preview:
  - matching: `assignments[]`, `unmatched[]`
  - monitoring: `flaggedItems[]`, `condition`, `alertRecipients[]`
  - analysis: `dimensions[] {name,current,goal?,progress?}`, `lapsedItems[]`, `totalAnalyzed`
- Displays `Object.entries(item.metrics)` (slice to 4 on card; all in modal)

## apps/web/src/lib/mockData.ts — FE demo fixtures

**Produces:** mock `ApprovalGate` (matching / monitoring / analysis) and a `WorkflowResult` for UI previews.

**Objects:**

- `mockMatchingApproval` (template: `matching`)
  - `params`: `{ sourceFile, targetFile, matchStrategy, notifications[] }`
  - `preview`: `{ assignments[], unmatched[], capacityWarnings[] }`
  - `metrics`: `{ fillRate, totalAssigned, totalVolunteers, rolesStaffed }`
- `mockMonitoringApproval` (template: `monitoring`)
  - `params`: `{ sourceFile, filterRules }`
  - `preview`: `{ flaggedItems[], alertRecipients[], condition }`
  - `metrics`: `{ flaggedCount, avgDaysSince, totalVisitors }`
- `mockAnalysisApproval` (template: `analysis`)
  - `params`: `{ sourceFile, targetFile }`
  - `preview`: `{ dimensions[] {name,current,goal?,progress?,trend?}, lapsedItems[], totalAnalyzed }`
  - `metrics`: `{ totalRaised, donorCount, lapsedCount, avgGift }`
- `mockMatchingResult` (status: `completed`)
  - `summary`, `completedAt`
  - `metrics`: `{ assigned, fillRate, messagesSent, rolesStaffed }`
  - `actions[]`: `{ type: 'assignment'|'notification', count, description }`

**Contracts used by UI:**  
`ApprovalGate { id, template, status, createdAt, params, preview, metrics }` • `WorkflowResult { id, template, status, completedAt, summary, metrics, actions }`

## packages/types/src/orchestrator.ts — Shared types (3-template + debate SSE)

**Templates & status:**  
`TemplateType = 'matching'|'monitoring'|'analysis'` • `ApprovalStatus = 'pending'|'approved'|'rejected'`

**Approval gate:**  
`ApprovalGate { id, template, status, createdAt, params: WorkflowParams, preview: (MatchingPreview|MonitoringPreview|AnalysisPreview), metrics: Record<string, number> }`

**Params:**  
`WorkflowParams { sourceFile, targetFile?, filterRules?, matchStrategy?: 'capacity_balanced'|'interest_overlap'|'proximity', notifications?: NotificationTemplate[] }`  
`NotificationTemplate { to: 'source'|'target'|'admin', channel: 'sms'|'email', message }`

**Matching preview:**  
`MatchingPreview { proposed_assignments: number, assignments_preview: MatchingAssignment[], match_rate: number, avg_match_score: number, source_count: number, target_count: number, notifications_planned: number, unmatched?: UnmatchedItem[], capacityWarnings?: string[] }`  
`MatchingAssignment { sourceId, sourceName, targetId, targetName, matchScore, matchReason }`  
`UnmatchedItem { id, name, reason }`

**Monitoring preview:**  
`MonitoringPreview { flaggedItems: FlaggedItem[], alertRecipients: string[], condition }`  
`FlaggedItem { id, name, lastContact: string|null, daysSince: number, phone?, email? }`

**Analysis preview:**  
`AnalysisPreview { dimensions: AnalysisDimension[], lapsedItems: LapsedItem[], totalAnalyzed: number }`  
`AnalysisDimension { name, current, goal?, progress?, trend: 'up'|'down'|'stable' }`  
`LapsedItem { id, name, lastDate, daysSince, lifetimeTotal? }`

**Result:**  
`WorkflowResult { id, template, status: 'completed'|'failed', completedAt, summary, metrics: Record<string, number|string>, actions: ResultAction[] }`  
`ResultAction { type: 'assignment'|'notification'|'calculation', count, description, details? }`

**Debate streaming:**  
`AgentName = 'Planner'|'Operations'|'HumanFlourishing'|'Moderator'`  
`DebateMessageType = 'proposal'|'rebuttal'|'vote'|'tiebreaker'`  
`DebateMessage { round: 1|2|3, agent, messageType, content, timestamp? }`  
`OrchestratorEventType = 'classifier_complete'|'debate_start'|'round_1_proposal'|'round_2_rebuttal'|'round_3_vote'|'voting_complete'|'preview_ready'|'error'|'complete'`  
`OrchestratorEvent { event: OrchestratorEventType, data: any }`  
Event payloads:

- `ClassifierCompleteData { template, confidence, reasoning }`
- `DebateMessageData { agent, round, messageType, content }`
- `VotingCompleteData { winner, voteTally: Record<AgentName, number>, winningStrategy, tieBrokenByModerator }`
- `PreviewReadyData { approvalId, workflowId, preview }`