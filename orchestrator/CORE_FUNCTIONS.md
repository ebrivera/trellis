# Trellis Orchestrator: Core Functions Reference

**Last Updated**: 2025-10-07

This document provides implementation details and usage examples for the 5 core functions that power the Trellis orchestrator.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Function 1: load_data()](#function-1-load_data)
3. [Function 2: filter_data()](#function-2-filter_data)
4. [Function 3: match()](#function-3-match)
5. [Function 4: calculate_metrics()](#function-4-calculate_metrics)
6. [Function 5: send_notification()](#function-5-send_notification)
7. [Integration Examples](#integration-examples)
8. [Testing](#testing)

---

## Architecture Overview

The Trellis orchestrator uses a workflow template architecture:

```
Natural Language Request
    ↓
Classifier (picks template: matching/monitoring/analysis)
    ↓
Extractor (fills parameters using LLM)
    ↓
Executor (runs workflow using 5 core functions)
    ↓
Approval Gate (human reviews before committing)
    ↓
Execution (creates records, sends notifications)
```

### Core Principles

1. **Separation of Concerns**: Each function has a single responsibility
2. **Type Safety**: Uses Pydantic models and enums
3. **DataFrame-Centric**: Data flows as pandas DataFrames
4. **Error Tolerance**: Graceful handling of partial failures

### Data Flow Example

```python
# 1. Load data
volunteers = await load_data(EntityType.PERSON, subtype='volunteer')

# 2. Filter
available = filter_data(volunteers, filters=[...])

# 3. Match
assignments = match(available, roles, strategy=..., match_fields=..., constraints=...)

# 4. Calculate metrics
metrics = calculate_metrics(formulas=[...], source_data=assignments_df)

# 5. Send notifications
await send_notification(recipients, config, global_vars)
```

---

## Function 1: load_data()

**File**: `src/functions/load_data.py`

### Purpose

Loads entities from Supabase and returns them as a pandas DataFrame.

### Why It's Simple

This function intentionally does only loading - no filtering, no transformation. Filtering was moved to a separate function to keep responsibilities clear and enable testing without a database.

### Signature

```python
async def load_data(
    entity_type: EntityType,
    subtype: Optional[str] = None
) -> pd.DataFrame
```

### How It Works

The function builds a SQL query based on the entity type and optional subtype:

1. **Base query**: `SELECT * FROM {table_name}`
2. **Add subtype filter** if provided (e.g., `WHERE person_type = 'volunteer'`)
3. **Execute query** with parameterized values to prevent SQL injection
4. **Convert to DataFrame** for easy manipulation

The two-tier entity system uses:
- **EntityType** (PERSON/GROUP/GIFT) → which table to query
- **subtype** (volunteer/role/initiative) → which type within the table

### EntityType Enum

```python
class EntityType(str, Enum):
    PERSON = "people"    # Maps to people table
    GROUP = "groups"     # Maps to groups table
    GIFT = "gifts"       # Maps to gifts table
```

### Usage Examples

#### Load all of a type
```python
volunteers = await load_data(EntityType.PERSON, subtype='volunteer')
roles = await load_data(EntityType.GROUP, subtype='role')
gifts = await load_data(EntityType.GIFT)  # No subtype for gifts
```

#### Load then filter
```python
all_volunteers = await load_data(EntityType.PERSON, subtype='volunteer')
filters = [FilterCondition(field='availability_days', operator='contains', value='Wed')]
wednesday_volunteers = filter_data(all_volunteers, filters)
```

---

## Function 2: filter_data()

**File**: `src/functions/filter.py`

### Purpose

Applies filter conditions to DataFrames with type-aware comparisons.

### Why Separate From Load

While SQL-level filtering is faster, Python filtering is more flexible for prototyping, easier to test without a database, and allows for complex compositions. The dataset sizes are small enough that performance isn't a concern.

### Signature

```python
def filter_data(
    df: pd.DataFrame,
    filters: Union[List[FilterCondition], List[dict]]
) -> pd.DataFrame
```

### Supported Operators

- `=` - equality
- `>`, `<`, `>=`, `<=` - comparisons
- `!=` - not equal
- `contains` - array containment

### How It Works

The function processes filters sequentially:

1. **Copy the DataFrame** to avoid mutating the original
2. **For each filter**:
   - Extract field, operator, and value
   - Convert value to the correct type (string → int/float/datetime)
   - Apply the appropriate pandas operation
3. **Return the filtered result**

### Type Conversion

A critical piece is `_convert_value()` which converts LLM-extracted strings to the proper types:

- Date fields (ending in `_date` or `_at`) → `datetime`
- Numeric strings → `int` or `float`
- Boolean strings → `bool`
- Everything else stays as `string`

This prevents errors like comparing an `int64` column to a string `"3"`.

### Usage Examples

#### Simple filter
```python
volunteers = await load_data(EntityType.PERSON, subtype='volunteer')
filters = [FilterCondition(field='capacity', operator='>', value='0')]
available = filter_data(volunteers, filters)
```

#### Multiple filters (AND logic)
```python
filters = [
    FilterCondition(field='availability_days', operator='contains', value='Sun'),
    FilterCondition(field='capacity', operator='>', value='0'),
    FilterCondition(field='interests', operator='contains', value='youth')
]
result = filter_data(volunteers, filters)
```

#### Time-relative filtering

For monitoring workflows, use `filter_by_time_condition()`:

```python
visitors = await load_data(EntityType.PERSON, subtype='visitor')

# Visitors from >14 days ago who we haven't contacted
old_visitors = filter_by_time_condition(
    visitors,
    time_field='visit_date',
    threshold='14 days',
    operator='>',
    additional_filters=['last_contact_date IS NULL']
)
```

**Note**: Time operators are inverted - `operator='>'` means "more than 14 days ago" which translates to `visit_date < (now - 14 days)`.

---

## Function 3: match()

**File**: `src/functions/match.py`

### Purpose

Matches source entities to target entities based on compatibility scoring with capacity constraints.

### Why Greedy Algorithm

The current implementation uses a greedy algorithm (each source picks the best available target) rather than globally optimal matching (Hungarian algorithm). This was chosen for simplicity and speed - it's easier to understand, debug, and fast enough for typical use cases (50 sources × 10 targets).

### Signature

```python
def match(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    strategy: MatchStrategy,
    match_fields: MatchFields,
    constraints: MatchConstraints
) -> List[Dict[str, Any]]
```

### Match Strategies

```python
class MatchStrategy(str, Enum):
    INTEREST_OVERLAP = "interest_overlap"      # Pure field similarity
    CAPACITY_BALANCED = "capacity_balanced"    # Field similarity + capacity bonus
    PROXIMITY = "proximity"                    # Geographic distance priority
```

### How It Works

The matching algorithm:

1. **Initialize capacity tracking** for each target (from constraints)
2. **For each source**:
   - Loop through all targets
   - Skip targets at capacity
   - Calculate match score using the chosen strategy
   - Skip scores below threshold
   - Track the best match
3. **Record assignment** if a match was found
4. **Decrement target capacity**

### Scoring System

The weighted scoring combines multiple fields:

1. **Build weight map** from `match_fields.weights`
2. **For each field** in `match_fields.score_on`:
   - Calculate field-specific score (0.0 to 1.0)
   - Multiply by field weight
   - Add to total score
3. **Cap at 1.0** to keep scores normalized

### Field Scoring by Type

Different data types are scored differently:

- **Arrays** (interests, skills): Jaccard similarity = |intersection| / |union|
- **Strings**: Exact match = 1.0, substring = 0.5, no match = 0.0
- **Numbers**: Normalized distance = 1 - (difference / max_value)
- **Other**: Exact equality = 1.0, otherwise 0.0

### Usage Examples

#### Simple matching
```python
volunteers = await load_data(EntityType.PERSON, subtype='volunteer')
roles = await load_data(EntityType.GROUP, subtype='role')

match_fields = MatchFields(
    score_on=['interests'],
    weights=[FieldWeight(field='interests', weight=1.0)]
)

constraints = MatchConstraints(
    max_per_target='capacity',
    min_score_threshold=0.3
)

assignments = match(
    volunteers,
    roles,
    MatchStrategy.INTEREST_OVERLAP,
    match_fields,
    constraints
)
```

#### Multi-field weighted
```python
match_fields = MatchFields(
    score_on=['interests', 'availability_days', 'zip'],
    weights=[
        FieldWeight(field='interests', weight=0.5),
        FieldWeight(field='availability_days', weight=0.3),
        FieldWeight(field='zip', weight=0.2)
    ]
)

assignments = match(volunteers, roles, MatchStrategy.CAPACITY_BALANCED, match_fields, constraints)
```

---

## Function 4: calculate_metrics()

**File**: `src/functions/calculate_metrics.py`

### Purpose

Calculates aggregate metrics and supports calculated expressions referencing other metrics.

### Why Limited DSL

Instead of supporting full SQL, we use a limited DSL that covers 90% of use cases (SUM, AVG, COUNT, GROUP BY, simple expressions). This is simpler to implement, easier to secure, and sufficient for the MVP.

### Signature

```python
def calculate_metrics(
    formulas: list[MetricFormula],
    source_data: pd.DataFrame
) -> Dict[str, Any]
```

### Supported Operations

- **Aggregations**: `SUM(col)`, `AVG(col)`, `COUNT(*)`, `COUNT(col)`, `COUNT(DISTINCT col)`, `MIN(col)`, `MAX(col)`
- **Grouping**: `group_by='column_name'`
- **Calculated**: `metric1 / metric2`, `amount * 1.1`

### How It Works

The function processes formulas sequentially:

1. **For each formula**:
   - Detect if it's an aggregation or calculated metric
   - **Aggregation**: Parse the SQL-like formula and execute on DataFrame
   - **Calculated**: Evaluate expression using previously calculated metrics
2. **Apply formatting** if specified (currency/percent/number)
3. **Store result** in results dict
4. **On error**: Store error message, continue processing

### Formula Types

**Aggregation formulas** are detected by regex pattern `(SUM|AVG|COUNT|MIN|MAX)(...)`:
- Extract operation and argument
- Handle GROUP BY if present
- Execute pandas aggregation

**Calculated formulas** have arithmetic operators but no aggregation function:
- Build safe context with previous metrics
- Use `eval()` with restricted builtins
- Convert result to float

### Usage Examples

#### Simple aggregation
```python
gifts = await load_data(EntityType.GIFT)

formulas = [
    MetricFormula(name='total_raised', formula='SUM(amount)')
]

results = calculate_metrics(formulas, gifts)
# {'total_raised': 15000.0}
```

#### Grouped aggregation
```python
formulas = [
    MetricFormula(
        name='total_by_initiative',
        formula='SUM(amount)',
        group_by='initiative_name'
    )
]

results = calculate_metrics(formulas, gifts)
# {'total_by_initiative': {'Building Fund': 5000.0, 'Youth Program': 10000.0}}
```

#### Multiple metrics with formatting
```python
formulas = [
    MetricFormula(name='total', formula='SUM(amount)', format='currency'),
    MetricFormula(name='count', formula='COUNT(*)', format='number'),
    MetricFormula(name='average', formula='AVG(amount)', format='currency')
]

results = calculate_metrics(formulas, gifts)
# {'total': '$15,000.00', 'count': '150', 'average': '$100.00'}
```

#### Calculated metrics

**Important**: Order matters! Dependencies must be calculated first.

```python
formulas = [
    MetricFormula(name='total_raised', formula='SUM(amount)'),
    MetricFormula(name='goal', formula='SUM(goal)'),
    MetricFormula(name='progress', formula='total_raised / goal', format='percent')
]

results = calculate_metrics(formulas, initiatives_df)
# {'total_raised': 7500.0, 'goal': 10000.0, 'progress': '75.0%'}
```

---

## Function 5: send_notification()

**File**: `src/functions/send_notification.py`

### Purpose

Queues notifications with template rendering for SMS or email delivery.

### Why Recipients Are Pre-Resolved

The `NotificationConfig` has a `recipient_type` field ('source', 'target', 'flagged'), but this function expects recipients to already be resolved. The template executor handles the resolution since it knows the workflow context (which DataFrame is 'source' vs 'target'). This keeps `send_notification()` simple and reusable.

### Why Simplified Handlebars

We use a simplified `{{variable}}` syntax instead of full Handlebars (with `{{#if}}` and `{{#each}}`). The current use cases only need simple variable substitution, and this avoids an external dependency. Can upgrade later if conditionals/loops are needed.

### Signature

```python
async def send_notification(
    recipients: List[Dict[str, Any]],
    config: NotificationConfig,
    global_variables: Optional[Dict[str, Any]] = None,
    db_insert: bool = True,
    workflow_run_id: Optional[str] = None
) -> Dict[str, Any]
```

### How It Works

The function processes recipients individually:

1. **For each recipient**:
   - Validate required fields (id, email/phone based on channel)
   - Render template by merging global and recipient variables
   - Build message record with all metadata
   - Add to messages list (or errors if validation fails)
2. **Insert to database** if `db_insert=True`
3. **Return summary** with sent count, failed count, messages, and errors

### Template Rendering

Templates use `{{variable}}` syntax with these features:

- **Simple variables**: `{{name}}` → looks up `name` in merged variables
- **Nested access**: `{{person.contact.email}}` → traverses nested dicts
- **Missing variables**: `{{unknown}}` → keeps placeholder as-is
- **Variable precedence**: Recipient variables override global variables

The regex pattern `\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}` matches variables with optional whitespace.

### Validation

Each recipient is validated based on the channel:
- **Always required**: `id` field
- **SMS channel**: `phone` field must be present and non-empty
- **Email channel**: `email` field must be present and non-empty

Validation errors are caught per-recipient, allowing partial success.

### Usage Examples

#### Simple SMS
```python
recipients = [
    {'id': 'v1', 'name': 'Alice', 'phone': '555-0001'},
    {'id': 'v2', 'name': 'Bob', 'phone': '555-0002'}
]

config = NotificationConfig(
    channel=Channel.SMS,
    template="Hi {{name}}, you're assigned to {{role}}!"
)

global_vars = {'role': 'Youth Leader'}

result = await send_notification(recipients, config, global_vars)
# {'sent': 2, 'failed': 0, 'messages': [...], 'errors': []}
```

#### Email with nested variables
```python
recipients = [
    {
        'id': 'm1',
        'email': 'alice@example.com',
        'person': {
            'name': 'Alice',
            'interests': ['music', 'teaching']
        }
    }
]

config = NotificationConfig(
    channel=Channel.EMAIL,
    template="Hi {{person.name}}, your interests: {{person.interests}}"
)

result = await send_notification(recipients, config, {})
```

#### Testing without database
```python
result = await send_notification(
    recipients,
    config,
    global_vars,
    db_insert=False  # Don't insert to DB
)

assert result['sent'] == 2
assert len(result['messages']) == 2
```

### Helper Functions

```python
# Preview template rendering (useful for approval UI)
preview = render_template_preview(
    template="Hi {{name}}, you're assigned to {{role}}!",
    sample_recipient={'name': 'Sample User'},
    global_variables={'role': 'Test Role'}
)
# → "Hi Sample User, you're assigned to Test Role!"

# Extract variable names from template (useful for validation)
vars = extract_template_variables("Hi {{name}}, role: {{role_name}}")
# → ['name', 'role_name']
```

---

## Integration Examples

### Matching Workflow

```python
# 1. Load data
volunteers = await load_data(EntityType.PERSON, subtype='volunteer')
roles = await load_data(EntityType.GROUP, subtype='role')

# 2. Filter both sides
volunteer_filters = [
    FilterCondition(field='availability_days', operator='contains', value='Sun'),
    FilterCondition(field='capacity', operator='>', value='0')
]
available_volunteers = filter_data(volunteers, volunteer_filters)

role_filters = [FilterCondition(field='capacity', operator='>', value='0')]
available_roles = filter_data(roles, role_filters)

# 3. Match
assignments = match(
    available_volunteers,
    available_roles,
    MatchStrategy.CAPACITY_BALANCED,
    match_fields,
    constraints
)

# 4. Calculate metrics
assignments_df = pd.DataFrame(assignments)
metrics = calculate_metrics([
    MetricFormula(name='match_rate', formula='COUNT(*) / ...'),
    MetricFormula(name='avg_score', formula='AVG(match_score)')
], assignments_df)

# 5. Send notifications
for assignment in assignments:
    volunteer = volunteers[volunteers['id'] == assignment['source_id']].iloc[0]
    await send_notification(
        [volunteer.to_dict()],
        NotificationConfig(
            channel=Channel.SMS,
            template="Hi {{name}}, you're assigned to {{target_name}}!"
        ),
        {'target_name': assignment['target_name']}
    )
```

### Monitoring Workflow

```python
# 1. Load data
visitors = await load_data(EntityType.PERSON, subtype='visitor')

# 2. Time-based filtering
flagged = filter_by_time_condition(
    visitors,
    time_field='visit_date',
    threshold='14 days',
    operator='>',
    additional_filters=['last_contact_date IS NULL']
)

# 3. Calculate metrics
metrics = calculate_metrics([
    MetricFormula(name='flagged_count', formula='COUNT(*)'),
    MetricFormula(name='avg_days_since_visit', formula='AVG(days_since_visit)')
], flagged)

# 4. Send alerts
leader_recipients = [{'id': 'leader1', 'email': 'leader@church.org'}]
await send_notification(
    leader_recipients,
    NotificationConfig(
        channel=Channel.EMAIL,
        template="Alert: {{count}} visitors need follow-up"
    ),
    {'count': metrics['flagged_count']}
)
```

### Analysis Workflow

```python
# 1. Load data
gifts = await load_data(EntityType.GIFT)
initiatives = await load_data(EntityType.GROUP, subtype='initiative')

# 2. Filter to recent gifts
recent_filters = [FilterCondition(field='gift_date', operator='>', value='2024-01-01')]
recent_gifts = filter_data(gifts, recent_filters)

# 3. Calculate grouped metrics
metrics = calculate_metrics([
    MetricFormula(
        name='total_by_initiative',
        formula='SUM(amount)',
        group_by='initiative_name',
        format='currency'
    ),
    MetricFormula(
        name='donor_count_by_initiative',
        formula='COUNT(DISTINCT donor)',
        group_by='initiative_name'
    )
], recent_gifts)

# 4. Send report
stakeholders = [{'id': 's1', 'email': 'stakeholder@church.org'}]
await send_notification(
    stakeholders,
    NotificationConfig(
        channel=Channel.EMAIL,
        template="Giving report: {{total_by_initiative}}"
    ),
    metrics
)
```

---

## Testing

### Test Organization

All test files are located in the `tests/` directory:

```
tests/test_load_data.py           (7 tests)   - Database loading
tests/test_filter.py              (16 tests)  - Filtering logic (no DB)
tests/test_match.py               (15 tests)  - Matching algorithms (no DB)
tests/test_calculate_metrics.py   (20 tests)  - Metrics calculation (no DB)
tests/test_send_notification.py   (20 tests)  - Notification queuing (no DB)
tests/test_integration.py         (5 tests)   - Load + filter integration (DB)
```

### Running Tests

**Important**: Run all tests from the `orchestrator/` directory using the venv Python:

```bash
# Individual test files (no database required)
./venv/bin/python tests/test_filter.py
./venv/bin/python tests/test_match.py
./venv/bin/python tests/test_calculate_metrics.py
./venv/bin/python tests/test_send_notification.py

# Database tests (requires running Supabase)
./venv/bin/python tests/test_load_data.py
./venv/bin/python tests/test_integration.py
```

### Testing Without Database

Most functions support database-free testing:

```python
# filter_data: Uses mock DataFrames
df = pd.DataFrame([{'name': 'Alice', 'capacity': 5}])
result = filter_data(df, [...])

# match: Uses mock DataFrames
volunteers_df = pd.DataFrame([...])
roles_df = pd.DataFrame([...])
assignments = match(volunteers_df, roles_df, ...)

# calculate_metrics: Uses mock DataFrames
df = pd.DataFrame([{'amount': 100}])
results = calculate_metrics([...], df)

# send_notification: Set db_insert=False
result = await send_notification(recipients, config, {}, db_insert=False)
```

---

**Total Test Coverage**: 83 tests across all functions
