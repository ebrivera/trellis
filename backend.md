# BACKEND Schema

### This is meant to be a markdown file that will explain the codebase

```
(venv) MacBookPro:trellis ernestorivera$ tree -I "venv|__pycache__|.next|node_modules"
.
(venv) MacBookPro:trellis ernestorivera$ tree -I "venv|__pycache__|.next|node_modules|test_*"
.
├── README.md
├── apps
│   └── web
│       ├── next-env.d.ts
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

## orchestrator/src/main.py — Orchestrator API (REST + SSE)

**Consumes:** FastAPI, `dotenv`; DB (`init_db_pool`, `close_db_pool`, `fetch_one`, `execute`); runners (`run_orchestration`, `run_orchestration_with_events`, `execute_workflow`)  
**Produces:** orchestration result, approval CRUD, live SSE events

**Lifecycle:** `startup → init_db_pool`, `shutdown → close_db_pool`; CORS: `http://localhost:3000,3001`

**Models:**

- `OrchestrateRequest { request: str, csv_urls?: Dict[str,str], available_files: str[] }`
- `OrchestrateResponse { approvalId, workflowId, template: str, params: dict, preview: dict, clarifications: str[] }`
- `ApprovalDecision { action: 'approve'|'reject', reason?: str }`

**Routes:**

- `GET /` → `{status:'alive', service:'trellis-orchestrator'}`
- `POST /orchestrate` → `run_orchestration(request, available_files)` → `OrchestrateResponse` (uses `template.value`, `debate_state.params`)
- `GET /approval/{approval_id}` → `SELECT * FROM approval_gates WHERE id=$1`
- `POST /approval/{approval_id}/decide`
    - approve → `UPDATE approval_gates ... status='approved'` → `execute_workflow(approval_id)` → `{status:'approved', result}`
    - reject → `UPDATE approval_gates ... status='rejected', rejection_reason` and `UPDATE workflow_runs ... status='rejected'` → `{status:'rejected'}`
- `GET /orchestrate/stream?request=...` → **SSE** from `run_orchestration_with_events(request, [], queue)`

**SSE format:**
event: <name>
data: <json>
…then `event: complete` / on error `event: error`.

**Notes:** Streaming uses an `asyncio.Queue` + background task; response headers disable buffering.

## orchestrator/src/graph_executor.py — Workflow executor (post-approval)

**Purpose:** Run approved workflows. Also generates dry-run previews for the approval UI.

**Exports (async):**

- `generate_preview(template, params, workflow_id) -> Dict`
    - Routes to `_preview_matching | _preview_monitoring | _preview_analysis`
- `execute_workflow(approval_id, approved_by='system') -> Dict`
    - Loads approval + workflow_run, dispatches by template, persists status/results
- `execute_matching(params, workflow_run_id) -> Dict`
- `execute_monitoring(params, workflow_run_id) -> Dict`
- `execute_analysis(params, workflow_run_id) -> Dict`

**Normalization safety net:**

- `normalize_match_fields(match_fields)` — maps synonyms → canonical columns  
    (`skills|abilities|talents|experience|skill|ability|talent → interests`, `availability* → availability_days`)  
    Applied in preview+execute for matching.

**Preview (no writes):**

- **matching** → loads `source_df`/`target_df` → optional `filter_data` → `match_func` → returns:  
    `{ proposed_assignments, match_rate, avg_match_score, assignments_preview(≤10), source_count, target_count, notifications_planned }`
- **monitoring** → load df → `filter_by_time_condition` →  
    `{ flagged_count, total_scanned, flagged_preview(≤10), notifications_planned }`
- **analysis** → load df → `calculate_metrics` →  
    `{ entities_analyzed, metrics_calculated, insights, recommendations: [] }`

**Execute (writes + side effects):**

- Common: parse `workflow.extracted_params` (json), `TemplateType` dispatch; on success `workflow_runs.status='completed'` with `results`; on error `status='failed'` with `error`.

- **matching**
    1. load/filter sources/targets
    2. `match_func` → `assignments`
    3. `insert_many("assignments", [{ source_id,target_id,target_type,assignment_type,match_score,status,workflow_run_id }])`
    4. notifications per `params_model.notifications` via `send_notification` (source / target / target_owners)
    5. return `{ assignments_created, notifications_sent, match_rate, avg_match_score }`

- **monitoring**
    1. load df → `filter_by_time_condition` → flagged
    2. notify flagged via `send_notification`
    3. return `{ flagged_count, notifications_sent }`

- **analysis**
    1. load df → `calculate_metrics`
    2. (notifications TODO)
    3. return `{ entities_analyzed, metrics, insights }`

**DB touched:**

- read: `approval_gates`, `workflow_runs`
- write: `assignments` (insert), `workflow_runs` (update status/results/error)

**Depends on:**  
`templates.(matching|monitoring|analysis).*Params`, `functions.(load_data|filter|match|send_notification|calculate_metrics)`, `database.(fetch_one|insert_many|execute)`, `schemas.TemplateType/EntityType`.

**Contracts:**

- params must match template Pydantic models; matching expects normalized `match_fields`.
- all returns are JSON-serializable (stored in `workflow_runs.results`).

## orchestrator/src/graph_streaming.py — Orchestration (SSE streaming)

**Purpose:** Run the debate graph and emit real-time SSE events per node completion.

**Export:**

- `run_orchestration_with_events(request, available_files, event_queue) -> Dict`

**Flow (LangGraph `.astream()`):**

- Build `initial_state` (`request`, `available_files`, flags/arrays)
- `graph = create_orchestrator_graph()`
- `async for output in graph.astream(initial_state):`
    - For each completed `node_name`, push SSE payloads to `event_queue`:

**Emitted events:**

- `classifier_complete` → `{ template, confidence, reasoning }`
- `debate_start` → `{ agents: ['Planner','Operations','HumanFlourishing'] }`
- `round_1_proposal` (per agent) → `{ agent, round:1, messageType:'proposal', content }`
- `round_2_rebuttal` (per agent) → `{ agent, round:2, messageType:'rebuttal', content }`
- `round_3_vote` (per agent) → `{ agent, round:3, messageType:'vote', content:'Voted for X' }`
- `voting_complete` → `{ winner, voteTally, winningStrategy, tieBrokenByModerator }`
- `preview_ready` → `{ approvalId, workflowId, preview, template }` (also captures `final_result`)

**Returns:** final state captured at `create_approval_gate`.

**Depends on:** `create_orchestrator_graph`, `schemas.TemplateType`, `asyncio.Queue` for SSE handoff.

---

## orchestrator/src/nodes/debate/orchestrator.py — Debate state manager

**Purpose:** Initialize/advance debate rounds and format context for agents/UI.

**Exports:**

- `initialize_debate_state(orchestrator_state) -> state`
    - Injects `debate_state` with: `current_round=1`, `{proposals,rebuttals,votes}`, `vote_tally`, `winning_agent`, `params`, `errors`
- `advance_to_round_2(state) -> state`
- `advance_to_round_3(state) -> state`
- `format_proposals_for_rebuttal(debate_state, current_agent) -> str`
- `format_debate_history_for_voting(debate_state) -> str`
- `get_active_agents(state) -> List[str]`

**Debate data (nested `debate_state`):**
`{ request, template, current_round, proposals, rebuttals, votes, debate_history, winning_agent, winning_strategy, vote_tally, params, agent_initiated, errors }`

**Depends on:** `schemas.(DebateState, OrchestratorState)` types (conceptually), `get_agent_configs()` for agent list.

# Backend — Schemas, DB Utils, and DB Schema

## orchestrator/src/schemas.py

**Purpose:** Shared Pydantic types for classifier → debate → approval → execution.

### Enums

- `Channel`: `sms | email`
- `EntityType`: `people | groups | gifts`
- `MatchStrategy`: `capacity_balanced | interest_overlap | proximity`
- `TemplateType`: `matching | monitoring | analysis`

### Debate

- `AgentConfig { name, persona_file, emoji, role_description }`
- `DebateMessage { round(1–3), agent, message_type('proposal'|'rebuttal'|'vote'), content, timestamp? }`
- `DebateState`
    - Input: `request, template`
    - Tracking: `current_round, proposals{}, rebuttals{}, votes{}, debate_history[]`
    - Results: `winning_agent?, winning_strategy?, vote_tally?`
    - `params?` (winner-extracted), `agent_initiated`, `errors[]`

### Shared building blocks

- `FilterCondition { field, operator, value }`
- `EntitySource (DEPRECATED)`
- `EntityQuery { entity_type, subtype?, filters? }` (+ subtype validation)
- `NotificationConfig { recipient_type?, recipient?, channel, template }` (at least one recipient\* specified)

### Classifier output

- `TemplateChoice { template, confidence, reasoning, clarifying_question? }`

### Orchestrator graph state

- `OrchestratorState`
    - Input: `request, available_files[], agent_initiated`
    - Classifier: `template?, confidence?, classifier_reasoning?`
    - Debate: `debate_state?, winning_agent?, winning_strategy?, vote_tally?, debate_history[]`
    - Extracted params: `params?`
    - Execution: `approval_id?, workflow_run_id?, execution_status?, preview_data?`
    - Errors: `errors[], clarifications[]`

### Approval previews

- `MatchingPreview { proposed_assignments, unmatched_source, unmatched_target, match_rate, avg_match_score, assignments_table[] }`
- `MonitoringPreview { flagged_count, avg_threshold_exceeded_by, flagged_entities[], alert_recipients[], optional_notification_count? }`
- `AnalysisPreview { metrics_summary{}, flagged_entities[]?, notification_count, dashboard_data{} }`

### Approval gate

- `ApprovalGate { id, template, params{}, preview_data{}, status('pending'|'approved'|'rejected'), created_at, resolved_at? }`

---

## orchestrator/src/database.py

**Purpose:** Async PostgreSQL access via `asyncpg` + small DAO helpers.

### Lifecycle

- `init_db_pool()` / `close_db_pool()` — manage global pool
- `get_pool()` — access pool
- `get_connection()` — async context manager

### Queries

- `fetch_all(sql, *args) -> List[dict]`
- `fetch_one(sql, *args) -> dict | None`
- `execute(sql, *args) -> str`

### Inserts

- `insert_one(table, data: dict) -> dict` (returns inserted row; dict/list values JSON-encoded)
- `insert_many(table, rows: List[dict]) -> int` (bulk insert; JSON-encode dict/list)

### Transactions

- `transaction_context()` — async context manager for multi-statement transactions

### Audit

- `log_function_call(function_name, params, result=None, workflow_run_id=None, user_id=None, duration_ms=None, error=None)`

> Helpers: `_prepare_data`, `_prepare_value` convert dict/list → JSON for JSONB columns.

---

## db/schema.sql (Trellis MVP)

**Purpose:** 8 tables for matching, monitoring, analysis + audit trail.

### 1) `people`

- Core person entity (`person_type`: volunteer|visitor|mentor|mentee|donor|leader)
- Matching fields: `interests TEXT[]`, `availability_days TEXT[]`, `capacity`
- Follow-up: `visit_date`, `last_contact_date`
- `metadata JSONB`, timestamps (+ `updated_at` trigger)

### 2) `groups`

- Roles/initiatives/teams (`group_type`)
- Matching/analysis: `requirements TEXT[]`, `capacity`, `current_count`, `goal`
- `leader_id → people(id)`, `metadata JSONB`, timestamps (+ trigger)

### 3) `assignments`

- Links people → groups/people
- Fields: `target_type('group'|'person')`, `assignment_type`, `match_score`, `status`
- `workflow_run_id` FK (+ indexes), timestamps (+ trigger)

### 4) `messages`

- Outbound notification log/queue
- `recipient_id → people`, `channel`, `content`, `status`, `sent_at`, `workflow_run_id`, `metadata`

### 5) `gifts`

- Financial records for analysis
- `donor_id → people`, `initiative_id → groups?`, `amount`, `gift_date`, `metadata`

### 6) `workflow_runs`

- Lifecycle of each orchestration
- `template_type`, `status`, `request_text`, `extracted_params JSONB`, `results JSONB`, `error`, timestamps

### 7) `approval_gates`

- Human-in-the-loop checkpoints
- `workflow_run_id UNIQUE → workflow_runs`, `gate_type`, `preview_data JSONB`, `metrics JSONB`, `status`, `approved_by`, `approved_at`, `rejection_reason`

### 8) `audit_log`

- Every function call: `function_name`, `params JSONB`, `result JSONB`, `workflow_run_id`, `duration_ms`, `error`, timestamp

### Indexes & Triggers

- Targeted indexes on foreign keys, statuses, types, timestamps
- `update_updated_at` trigger for `people`, `groups`, `assignments`
