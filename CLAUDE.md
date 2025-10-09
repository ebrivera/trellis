# Trellis - AI-Powered Church Workflow Automation

## Project Overview

**Trellis** is a natural-language workflow orchestration system designed for church operations. It enables non-technical staff to automate complex tasks like volunteer matching, visitor follow-ups, and giving analysis using plain English requests.

### Core Philosophy

- **Human-in-the-Loop AI**: Every workflow pauses for human approval before executing actions
- **Multi-Agent Debate**: Three AI agents (Planner, Operations, HumanFlourishing) debate the best approach before execution
- **Template-Based**: Three fixed workflow templates cover 90% of church automation needs
- **CSV-First**: Works with uploaded spreadsheets, no complex integrations required

### Technology Stack

**Frontend (Next.js 14)**

- Framework: Next.js 14 with App Router
- Language: TypeScript
- UI: Tailwind CSS + custom components
- State: React hooks (no external state management)
- Monorepo: Turborepo with npm workspaces

**Backend (Python/FastAPI)**

- Framework: FastAPI (async/await)
- AI: LangGraph for multi-agent orchestration
- LLM: OpenAI GPT-4o
- Database: PostgreSQL (via Supabase)
- Data Processing: pandas

**Architecture Pattern**

- Frontend: Server-Side Events (SSE) for real-time updates
- Backend: LangGraph state machine with debate nodes
- Data: Shared TypeScript types across frontend/backend

---

## Project Structure

```
trellis/
├── apps/
│   └── web/                    # Next.js frontend application
│       ├── src/
│       │   ├── app/           # Next.js app router pages
│       │   │   ├── page.tsx                    # Dashboard (home)
│       │   │   ├── plan/page.tsx              # Chat-based planner (main UI)
│       │   │   ├── approvals/page.tsx         # Approval queue
│       │   │   ├── results/[id]/page.tsx      # Workflow results
│       │   │   ├── settings/page.tsx          # Settings & data import
│       │   │   └── layout.tsx                 # Root layout with navbar
│       │   ├── components/
│       │   │   ├── layout/                    # Navbar, Background, ProfileDropdown
│       │   │   └── ui/                        # Reusable UI components
│       │   │       ├── ApprovalItem.tsx       # Single approval card
│       │   │       ├── DebateViewer.tsx       # 3-agent debate panel
│       │   │       ├── ChatMessage.tsx        # Chat bubble component
│       │   │       ├── Button.tsx, Badge.tsx, Card.tsx, Modal.tsx
│       │   │       └── PlanCard.tsx
│       │   └── lib/
│       │       ├── api.ts                     # Backend API client (currently mocks)
│       │       ├── mockData.ts                # Demo fixtures for UI development
│       │       └── utils.ts                   # Utility functions
│       └── package.json
│
├── orchestrator/                # Python backend orchestrator
│   ├── src/
│   │   ├── main.py                            # FastAPI server (REST + SSE endpoints)
│   │   ├── graph.py                           # LangGraph orchestration graph
│   │   ├── graph_executor.py                  # Workflow executor (post-approval)
│   │   ├── graph_streaming.py                 # SSE streaming wrapper
│   │   ├── database.py                        # PostgreSQL async helpers
│   │   ├── schemas.py                         # Pydantic models (shared types)
│   │   ├── nodes/
│   │   │   ├── classifier.py                  # Template classifier node
│   │   │   └── debate/
│   │   │       ├── agent.py                   # Agent execution logic
│   │   │       ├── extract_params.py          # Extract params from winner
│   │   │       ├── orchestrator.py            # Debate state manager
│   │   │       ├── tiebreaker.py              # Moderator tie-breaking
│   │   │       └── voting.py                  # Vote tallying
│   │   ├── functions/
│   │   │   ├── load_data.py                   # Load entities from DB
│   │   │   ├── filter.py                      # Filter DataFrames
│   │   │   ├── match.py                       # Matching algorithm
│   │   │   ├── calculate_metrics.py           # Metrics aggregation
│   │   │   └── send_notification.py           # Notification queuing
│   │   └── templates/
│   │       ├── matching.py                    # Matching template params
│   │       ├── monitoring.py                  # Monitoring template params
│   │       └── analysis.py                    # Analysis template params
│   ├── prompts/
│   │   ├── agent_personas/                    # Agent personality prompts
│   │   │   ├── planner.txt                    # Strategic, data-driven
│   │   │   ├── operations.txt                 # Pragmatic, implementable
│   │   │   ├── human_flourishing.txt          # People-focused, relational
│   │   │   └── moderator.txt                  # Tie-breaker
│   │   ├── classify_template.txt              # Template classification prompt
│   │   └── extract_params_*.txt               # Parameter extraction prompts
│   ├── tests/                                 # 83 tests across all functions
│   ├── requirements.txt
│   └── CORE_FUNCTIONS.md                      # Detailed function documentation
│
├── packages/
│   ├── types/                                 # Shared TypeScript types
│   │   └── src/
│   │       ├── index.ts
│   │       └── orchestrator.ts                # Core workflow types
│   └── utils/                                 # Shared utilities
│
├── supabase/
│   ├── migrations/
│   │   └── 20251006000001_initial_schema.sql  # 8-table schema
│   ├── config.toml
│   └── seed.sql
│
├── frontend.md                                # Frontend architecture doc
├── backend.md                                 # Backend architecture doc
├── README.md                                  # Dev setup instructions
├── package.json                               # Root workspace config
└── turbo.json                                 # Turborepo config
```

---

## Core Concepts

### 1. The Three Workflow Templates

All workflows route to one of three templates:

#### **Matching Template**

- **Purpose**: Assign source entities to target entities with compatibility scoring
- **Use Cases**:
  - Volunteers → Roles (based on interests, availability, skills)
  - Mentees → Mentors (based on interests, location, capacity)
  - People → Groups/Teams
- **Algorithm**: Greedy matching with weighted field scoring
- **Key Fields**: `interests`, `availability_days`, `capacity`, `requirements`
- **Preview**: Shows proposed assignments, unmatched entities, capacity warnings
- **Files**: `orchestrator/src/templates/matching.py`, `orchestrator/src/functions/match.py`

#### **Monitoring Template**

- **Purpose**: Detect entities that meet time-based conditions and send alerts
- **Use Cases**:
  - Visitor follow-ups (visited >14 days ago, no contact)
  - Lapsed donors (no gift in 90 days)
  - Inactive volunteers (haven't served in 60 days)
- **Algorithm**: Time-based filtering with configurable thresholds
- **Key Fields**: `visit_date`, `last_contact_date`, `gift_date`
- **Preview**: Shows flagged entities, days since last activity, alert recipients
- **Files**: `orchestrator/src/templates/monitoring.py`, `orchestrator/src/functions/filter.py`

#### **Analysis Template**

- **Purpose**: Aggregate data across dimensions and calculate metrics
- **Use Cases**:
  - Giving analysis by initiative (total raised, donor count, progress to goal)
  - Capacity analysis (roles filled vs. total capacity)
  - Engagement trends (attendance over time)
- **Algorithm**: Grouped aggregations with calculated metrics
- **Key Fields**: `amount`, `goal`, `current_count`, `capacity`
- **Preview**: Shows metrics by dimension, lapsed items, progress indicators
- **Files**: `orchestrator/src/templates/analysis.py`, `orchestrator/src/functions/calculate_metrics.py`

### 2. Multi-Agent Debate System

Before executing any workflow, three AI agents debate the best approach:

#### **Agent Personalities** (see `orchestrator/prompts/agent_personas/`)

1. **Planner** (Strategic)
   - Priorities: Maximize coverage, balance capacity, optimize metrics
   - Thinking: Data-driven, scalable, systematic
   - Example: "Prioritize filling high-capacity roles to maximize volunteer impact"

2. **Operations** (Pragmatic)
   - Priorities: Feasibility, staff burden, existing processes
   - Thinking: Implementable, realistic, workload-aware
   - Example: "Avoid over-notification fatigue; cap at 2 messages per person per week"

3. **HumanFlourishing** (Relational)
   - Priorities: Personal connection, spiritual growth, relationship quality
   - Thinking: People-first, relational, holistic
   - Example: "Match mentors with mentees based on shared life experiences, not just availability"

4. **Moderator** (Tie-Breaker)
   - Only invoked if voting is tied
   - Balances all three perspectives

#### **Debate Flow** (see `orchestrator/src/graph.py`)

```
Round 1: Proposals
  Each agent proposes their strategy (e.g., match strategy, notification approach)

Round 2: Rebuttals
  Agents critique others' proposals and refine their own

Round 3: Voting
  Each agent votes for one approach (can't vote for themselves)

Tie-Breaking (if needed)
  Moderator weighs arguments and casts deciding vote

Winner Extraction
  Winning agent's parameters are extracted and used for execution
```

### 3. Human-in-the-Loop Approval

Every workflow creates an **Approval Gate** before execution:

1. **Preview Generation**: Dry-run execution shows what will happen
2. **Approval UI**: User reviews proposed actions in `/approvals` page
3. **Decision**: User approves (→ execution) or rejects (→ cancellation)
4. **Execution**: Only approved workflows write to database

**Approval Gate Fields** (`approval_gates` table):

- `preview_data`: JSON of what will happen (assignments, notifications, etc.)
- `metrics`: High-level stats (match_rate, flagged_count, total_raised)
- `status`: `pending` | `approved` | `rejected`

### 4. The Five Core Functions

All workflow logic is built from five composable functions (see `orchestrator/CORE_FUNCTIONS.md`):

1. **`load_data(entity_type, subtype)`** - Load entities from database
2. **`filter_data(df, filters)`** - Apply conditions to DataFrame
3. **`match(source_df, target_df, strategy, fields, constraints)`** - Match entities
4. **`calculate_metrics(formulas, source_data)`** - Aggregate and calculate
5. **`send_notification(recipients, config, variables)`** - Queue notifications

**Design Principle**: Each function is:

- **Testable**: 83 tests, most work without database
- **Composable**: Functions chain together for complex workflows
- **Auditable**: Every call logged to `audit_log` table

---

## Database Schema

8 tables in PostgreSQL (see `supabase/migrations/20251006000001_initial_schema.sql`):

### Entity Tables

1. **`people`** - Universal person entity
   - Types: `volunteer`, `visitor`, `mentor`, `mentee`, `donor`, `leader`
   - Matching: `interests[]`, `availability_days[]`, `capacity`
   - Monitoring: `visit_date`, `last_contact_date`

2. **`groups`** - Roles, initiatives, teams
   - Types: `role`, `initiative`, `team`
   - Matching: `requirements[]`, `capacity`, `current_count`
   - Analysis: `goal`, `current_count`

3. **`gifts`** - Financial records
   - Fields: `donor_id`, `initiative_id`, `amount`, `gift_date`

### Workflow Tables

4. **`workflow_runs`** - Lifecycle of each orchestration
   - Fields: `template_type`, `status`, `request_text`, `extracted_params`, `results`

5. **`approval_gates`** - Human review checkpoints
   - Fields: `workflow_run_id`, `preview_data`, `metrics`, `status`

6. **`assignments`** - Matches created by workflow
   - Fields: `source_id`, `target_id`, `match_score`, `workflow_run_id`

7. **`messages`** - Notification queue
   - Fields: `recipient_id`, `channel`, `content`, `status`, `workflow_run_id`

8. **`audit_log`** - Function call trace
   - Fields: `function_name`, `params`, `result`, `duration_ms`

---

## Data Flow

### Request → Approval Flow (SSE Streaming)

```
User submits request in /plan page
  ↓
Frontend opens SSE connection to /orchestrate/stream
  ↓
Backend: Classifier determines template (matching/monitoring/analysis)
  → SSE: classifier_complete
  ↓
Backend: Initialize debate with 3 agents
  → SSE: debate_start
  ↓
Backend: Round 1 - Each agent proposes strategy
  → SSE: round_1_proposal (3 events)
  ↓
Backend: Round 2 - Each agent rebuts
  → SSE: round_2_rebuttal (3 events)
  ↓
Backend: Round 3 - Each agent votes
  → SSE: round_3_vote (3 events)
  ↓
Backend: Tally votes, determine winner (+ tie-breaker if needed)
  → SSE: voting_complete
  ↓
Backend: Extract params from winning strategy
  ↓
Backend: Generate preview (dry-run execution)
  ↓
Backend: Create approval_gate + workflow_run records
  → SSE: preview_ready
  ↓
Frontend: Fetch full approval details via GET /approval/{id}
  ↓
Frontend: Display approval card with preview
  ↓
User reviews and clicks Approve/Reject
```

### Approval → Execution Flow

```
User clicks Approve in /approvals page
  ↓
Frontend: POST /approval/{id}/decide with action: 'approve'
  ↓
Backend: Update approval_gate.status = 'approved'
  ↓
Backend: Load workflow_run and extracted_params
  ↓
Backend: Route to template executor (matching/monitoring/analysis)
  ↓
Template Executor:
  1. Load data (load_data)
  2. Filter data (filter_data)
  3. Execute template logic (match/calculate_metrics/filter_by_time)
  4. Write results (insert assignments, queue notifications)
  5. Update workflow_run.status = 'completed'
  ↓
Backend: Return result summary
  ↓
Frontend: Navigate to /results/{resultId}
  ↓
Results page: Display completed actions, metrics, audit trail
```

---

## Key Components

### Frontend Components

#### **`apps/web/src/app/plan/page.tsx`** - Main Chat Planner

- **Role**: Primary user interface for creating workflows
- **Features**:
  - Chat-style interaction with message history
  - Embedded debate viewer showing 3-agent discussion
  - Template-specific approval preview cards
  - CSV URL or file upload
  - Quick action templates (matching/monitoring/analysis examples)
- **State**: `messages[]`, `debateData`, `currentApproval`, `isProcessing`
- **SSE Events**: Updates debate in real-time as agents debate

#### **`apps/web/src/components/ui/DebateViewer.tsx`** - Multi-Agent Debate Panel

- **Role**: 3-column display of agent proposals, rebuttals, votes
- **Features**:
  - Round selector (1: Proposals, 2: Rebuttals, 3: Voting)
  - Per-agent message history with expand/collapse
  - Winner badge and vote tallies
  - Color-coded agents (Planner=blue, Operations=green, HumanFlourishing=purple)
- **Props**: `messages: Record<AgentName, DebateMessage[]>`, `currentRound`, `winner`, `voteTally`

#### **`apps/web/src/app/approvals/page.tsx`** - Approval Queue

- **Role**: Review and approve/reject pending workflows
- **Features**:
  - Tabs: Pending / Approved / Rejected
  - Template-specific preview rendering:
    - Matching: Assignments table with unmatched warnings
    - Monitoring: Flagged items list with alert recipients
    - Analysis: Dimension cards with progress bars
  - Metrics summary (match_rate, flagged_count, etc.)
  - Approve/Reject/View Details actions
- **State**: `pendingItems[]`, `approvedItems[]`, `rejectedItems[]`, `selectedItem`, `modalOpen`

#### **`apps/web/src/app/results/[id]/page.tsx`** - Workflow Results

- **Role**: Show completed workflow outcomes
- **Features**:
  - Status badge (completed/failed)
  - Key metrics grid
  - Actions completed list (assignments created, notifications sent)
  - Export report (placeholder)
  - Navigation to create another workflow
- **Data**: `WorkflowResult` (status, metrics, actions[])

### Backend Components

#### **`orchestrator/src/main.py`** - FastAPI Server

- **Endpoints**:
  - `GET /` - Health check
  - `POST /orchestrate` - Run workflow (legacy, synchronous)
  - `GET /orchestrate/stream` - SSE streaming orchestration
  - `GET /approval/{id}` - Fetch approval gate
  - `POST /approval/{id}/decide` - Approve/reject workflow
- **CORS**: Allows `localhost:3000`, `localhost:3001`
- **Lifecycle**: `init_db_pool()` on startup, `close_db_pool()` on shutdown

#### **`orchestrator/src/graph.py`** - LangGraph Orchestration

- **Nodes**:
  1. `classifier` - Determine template (matching/monitoring/analysis)
  2. `initialize_debate` - Set up debate state
  3. `round_1_proposals` - All agents propose
  4. `advance_to_round_2` - Increment round counter
  5. `round_2_rebuttals` - All agents rebut
  6. `advance_to_round_3` - Increment round counter
  7. `round_3_voting` - All agents vote
  8. `tally_votes` - Determine winner (+ tie-breaker)
  9. `extract_params` - Extract params from winning strategy
  10. `create_approval_gate` - Generate preview, create DB records
- **Flow**: Linear graph (START → classifier → ... → create_approval_gate → END)

#### **`orchestrator/src/graph_executor.py`** - Workflow Executor

- **Functions**:
  - `generate_preview(template, params, workflow_id)` - Dry-run execution
  - `execute_workflow(approval_id, approved_by)` - Post-approval execution
  - `execute_matching(params, workflow_run_id)` - Matching template executor
  - `execute_monitoring(params, workflow_run_id)` - Monitoring template executor
  - `execute_analysis(params, workflow_run_id)` - Analysis template executor
- **Safety**: `normalize_match_fields()` maps synonyms → canonical columns

#### **`orchestrator/src/graph_streaming.py`** - SSE Event Stream

- **Function**: `run_orchestration_with_events(request, available_files, event_queue)`
- **Emits**:
  - `classifier_complete` → template, confidence, reasoning
  - `debate_start` → agents list
  - `round_1_proposal` → agent, content (×3)
  - `round_2_rebuttal` → agent, content (×3)
  - `round_3_vote` → agent, content (×3)
  - `voting_complete` → winner, voteTally, winningStrategy
  - `preview_ready` → approvalId, workflowId, preview

---

## Development Workflow

### Setup

**Frontend:**

```bash
# Install dependencies
corepack enable
corepack prepare npm@9.8.1 --activate
npm ci --include=dev

# Run dev server (http://localhost:3000)
npm run dev -w @trellis/web

# Or run all workspaces
npm run dev
```

**Backend:**

```bash
cd orchestrator

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI (http://localhost:8000)
uvicorn src.main:app --reload
```

**Database (Supabase):**

```bash
# Start local Supabase
supabase start

# Run migrations
supabase db reset

# Seed data
psql postgres://postgres:postgres@localhost:54322/postgres < supabase/seed.sql
```

### Running Tests

**Backend (83 tests):**

```bash
cd orchestrator

# Database-free tests (most functions)
./venv/bin/python tests/test_filter.py
./venv/bin/python tests/test_match.py
./venv/bin/python tests/test_calculate_metrics.py
./venv/bin/python tests/test_send_notification.py

# Database tests (requires Supabase running)
./venv/bin/python tests/test_load_data.py
./venv/bin/python tests/test_integration.py
```

### Common Tasks

#### Add a New Workflow Template

1. **Define Pydantic model**: `orchestrator/src/templates/new_template.py`
2. **Add to TemplateType enum**: `orchestrator/src/schemas.py`
3. **Update classifier prompt**: `orchestrator/prompts/classify_template.txt`
4. **Create param extraction prompt**: `orchestrator/prompts/extract_params_new_template.txt`
5. **Add executor**: `orchestrator/src/graph_executor.py` → `execute_new_template()`
6. **Add preview generator**: `orchestrator/src/graph_executor.py` → `_preview_new_template()`
7. **Update TypeScript types**: `packages/types/src/orchestrator.ts`
8. **Add UI preview component**: `apps/web/src/app/approvals/page.tsx`

#### Modify Agent Behavior

1. **Edit persona**: `orchestrator/prompts/agent_personas/{planner|operations|human_flourishing}.txt`
2. **Adjust priorities**: Change numbered list in persona file
3. **Test**: Run orchestration and observe debate in frontend DebateViewer

#### Add a Core Function

1. **Implement**: `orchestrator/src/functions/new_function.py`
2. **Write tests**: `orchestrator/tests/test_new_function.py` (aim for database-free)
3. **Document**: Update `orchestrator/CORE_FUNCTIONS.md`
4. **Integrate**: Call from template executors in `graph_executor.py`

#### Debug SSE Streaming

1. **Backend logs**: Watch FastAPI console for `print()` statements in nodes
2. **Frontend DevTools**: Network tab → filter "stream" → EventStream messages
3. **State inspection**: Add `print(state)` in graph nodes to see full state
4. **Manual SSE test**:
   ```bash
   curl -N "http://localhost:8000/orchestrate/stream?request=Match%20volunteers"
   ```

---

## Common Patterns

### Pattern: Template Executor

All template executors follow this pattern:

```python
async def execute_template(params: TemplateParams, workflow_run_id: str) -> Dict[str, Any]:
    """Execute template workflow"""
    try:
        # 1. Load data
        source_df = await load_data(params.source.entity_type, params.source.subtype)

        # 2. Filter data
        if params.source.filters:
            source_df = filter_data(source_df, params.source.filters)

        # 3. Execute template logic
        results = template_specific_logic(source_df, params)

        # 4. Write results (assignments, notifications, etc.)
        if results:
            await insert_many("table_name", results)

        # 5. Send notifications
        if params.notifications:
            for notification in params.notifications:
                await send_notification(recipients, notification, global_vars)

        # 6. Update workflow status
        await execute(
            "UPDATE workflow_runs SET status='completed', results=$1 WHERE id=$2",
            json.dumps(summary), workflow_run_id
        )

        return summary
    except Exception as e:
        # Log error, update workflow status
        await execute(
            "UPDATE workflow_runs SET status='failed', error=$1 WHERE id=$2",
            str(e), workflow_run_id
        )
        raise
```

### Pattern: Agent Node

All agent nodes follow this pattern:

```python
def execute_agent_action(agent_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute single agent action in current round"""
    debate_state = state['debate_state']
    current_round = debate_state['current_round']

    # 1. Build context from previous rounds
    if current_round == 1:
        context = format_request_for_proposal(debate_state)
    elif current_round == 2:
        context = format_proposals_for_rebuttal(debate_state, agent_name)
    else:
        context = format_debate_history_for_voting(debate_state)

    # 2. Call LLM with agent persona
    response = llm.invoke([
        {"role": "system", "content": load_persona(agent_name)},
        {"role": "user", "content": context}
    ])

    # 3. Store message in debate state
    message = DebateMessage(
        round=current_round,
        agent=agent_name,
        message_type=get_message_type(current_round),
        content=response.content
    )

    if current_round == 1:
        debate_state['proposals'][agent_name] = message
    elif current_round == 2:
        debate_state['rebuttals'][agent_name] = message
    else:
        debate_state['votes'][agent_name] = message

    return state
```

### Pattern: SSE Event Emission

```python
async def stream_orchestration():
    queue = asyncio.Queue()

    async def event_generator():
        while True:
            event = await queue.get()
            if event is None:  # Sentinel for completion
                break
            yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"

    # Run orchestration in background
    asyncio.create_task(run_orchestration_with_events(request, files, queue))

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## Environment Variables

**Frontend** (`apps/web/.env.local`):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend URL
```

**Backend** (`orchestrator/.env`):

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Database (Supabase local)
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres

# Twilio (for SMS notifications)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# Mailgun (for email notifications)
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=...
```

---

## Git Workflow

**Branch Structure:**

- `main` - Production-ready code
- `dev` - Integration branch
- Feature branches: `username/feature-name` (e.g., `jiehoon/dashboard-ui`)

**Current Branch:** `jiehoon/agent-robust`

- Focus: Graceful failure handling for agents that fail to find matches/assignments/results
- Recent commits: Field mismatch fixes, mock data additions

**Clean Status:** Working tree is clean (no uncommitted changes)

---

## Key Design Decisions

### Why Three Templates Instead of Dynamic Schema?

- **Speed**: Fixed templates are faster to build, test, and debug
- **Quality**: Hand-tuned prompts and logic for each template
- **Coverage**: These three cover 90% of church automation use cases
- **Simplicity**: Users don't need to understand schema design

### Why Greedy Matching Instead of Optimal?

- **Simplicity**: Easier to understand and debug
- **Speed**: O(n×m) is fast enough for typical sizes (50 volunteers × 10 roles)
- **Good Enough**: Greedy gets 95%+ of optimal quality in practice
- **Transparency**: Easy to explain why volunteer X matched to role Y

### Why Debate Instead of Single LLM?

- **Robustness**: Multiple perspectives catch edge cases
- **Transparency**: User sees reasoning, not just final answer
- **Alignment**: Balances competing priorities (efficiency vs. relationships vs. feasibility)
- **Trust**: Humans trust decisions more when they see deliberation

### Why Approval Gates Instead of Auto-Execute?

- **Safety**: Prevents AI mistakes from affecting real people
- **Trust**: Users trust system more when they have final say
- **Learning**: Approval feedback can train future models
- **Compliance**: Some actions legally require human oversight

### Why CSV Instead of API Integrations?

- **Simplicity**: Non-technical staff can export from any system
- **Privacy**: Data stays local, no OAuth flows
- **Flexibility**: Works with any church management system
- **Speed**: Faster MVP without integration maintenance

---

## Troubleshooting

### Issue: SSE events not appearing in frontend

- **Check**: Backend FastAPI console for node execution logs
- **Check**: Browser DevTools → Network → "stream" request → EventStream tab
- **Check**: CORS settings in `main.py` include frontend URL
- **Fix**: Ensure no buffering (headers disable buffering in `graph_streaming.py`)

### Issue: Debate agents not voting correctly

- **Check**: Agent persona files have clear voting instructions
- **Check**: Vote parsing in `orchestrator/src/nodes/debate/voting.py`
- **Debug**: Print `debate_state['votes']` before tallying
- **Fix**: Ensure agents can't vote for themselves (enforced in `voting.py`)

### Issue: Match function returning no assignments

- **Check**: Field names match between source and target DataFrames
- **Check**: `normalize_match_fields()` in `graph_executor.py` for synonyms
- **Check**: `min_score_threshold` isn't too high
- **Debug**: Print source/target DataFrames to verify column names
- **Fix**: Use exact column names or add synonyms to normalizer

### Issue: Database connection errors

- **Check**: Supabase is running (`supabase status`)
- **Check**: `DATABASE_URL` in `.env` matches Supabase local URL
- **Check**: Migrations applied (`supabase db reset`)
- **Fix**: Restart Supabase (`supabase stop && supabase start`)

### Issue: Preview not matching execution results

- **Root Cause**: Preview uses copy of data, execution uses live data
- **Check**: Time between preview and execution (data may have changed)
- **Fix**: Ensure preview and execution use same data snapshot
- **Mitigation**: Add timestamp to approval gate showing when preview was generated

---

## Resources

- **Docs**:
  - Frontend schema: `frontend.md`
  - Backend schema: `backend.md`
  - Core functions: `orchestrator/CORE_FUNCTIONS.md`
  - Database schema: `supabase/migrations/20251006000001_initial_schema.sql`

- **External Docs**:
  - LangGraph: https://langchain-ai.github.io/langgraph/
  - FastAPI: https://fastapi.tiangolo.com/
  - Next.js App Router: https://nextjs.org/docs/app
  - Supabase: https://supabase.com/docs

- **Testing**:
  - 83 backend tests in `orchestrator/tests/`
  - Most tests are database-free (use mock DataFrames)
  - Coverage: load_data (7), filter (16), match (15), calculate_metrics (20), send_notification (20), integration (5)

---

## Current Status (as of 2025-10-08)

**Branch:** `jiehoon/agent-robust`
**Recent Work:**

- Added graceful failure handling for agents that fail to find matches/assignments/results
- Fixed field mismatches between agent outputs and expected schemas
- Added more mock data for UI development

**Next Steps:**

- Complete robust error handling for all agent failure modes
- Test edge cases (no matches, tie votes, malformed params)
- Connect frontend to real backend (replace mock API)
- Add file upload for CSV (currently only URL input works)

**Known Gaps:**

- Frontend still uses mock data (`lib/mockData.ts`)
- File upload not wired to backend yet
- No authentication/authorization
- Notifications are queued but not sent (test mode)
- Results page doesn't fetch from real backend

---

## Contributing Guidelines

### Code Style

- **Frontend**: Prettier + ESLint (run `npm run format`)
- **Backend**: Black + isort (configure in `pyproject.toml`)
- **TypeScript**: Strict mode enabled
- **Python**: Type hints required for public functions

### Commit Messages

```
(type): brief description

Longer explanation if needed
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Example:

```
(feat): add capacity warnings to matching preview

Display warnings when roles are over-subscribed or under-utilized.
Updates both preview generation and approval UI.
```

### Pull Requests

1. Branch from `dev` (not `main`)
2. Keep PRs focused (one feature/fix per PR)
3. Update relevant docs (`frontend.md`, `backend.md`, this file)
4. Add tests for new functions
5. Ensure all tests pass before requesting review

---

## Glossary

- **Template**: One of three workflow types (matching, monitoring, analysis)
- **Approval Gate**: Human review checkpoint before workflow execution
- **Debate**: Multi-agent discussion to determine best strategy
- **Preview**: Dry-run execution showing what will happen if approved
- **Entity**: Person, group, or gift record in database
- **Assignment**: Match between source and target (volunteer → role)
- **Workflow Run**: Single execution of a workflow from request to completion
- **SSE**: Server-Sent Events, one-way real-time stream from backend to frontend
- **Capacity**: Maximum number of assignments a target can receive
- **Match Score**: 0.0-1.0 compatibility score between source and target
- **Flagged Item**: Entity meeting monitoring condition (visitor needing follow-up)

---

**Last Updated:** 2025-10-08
**Maintained By:** Development Team
**Questions?** See `README.md` for dev setup or `CORE_FUNCTIONS.md` for function details.
