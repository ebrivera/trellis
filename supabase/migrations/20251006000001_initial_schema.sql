-- Trellis MVP Initial Schema
-- 8 tables supporting matching, monitoring, and analysis workflows

-- 1. PEOPLE TABLE
-- Universal person entity: volunteers, visitors, mentors, mentees, donors, leaders
CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT, -- ID from uploaded CSV
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    person_type TEXT NOT NULL, -- 'volunteer', 'visitor', 'mentor', 'mentee', 'donor', 'leader'
    interests TEXT[], -- Array for matching (e.g., ['youth', 'music'])
    availability_days TEXT[], -- Array (e.g., ['Mon', 'Sun'])
    capacity INTEGER, -- For mentors/leaders: how many they can support
    visit_date TIMESTAMP, -- For visitors: first visit date
    last_contact_date TIMESTAMP, -- For follow-up tracking
    metadata JSONB, -- Flexible storage for CSV extras
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. GROUPS TABLE
-- Roles, initiatives, teams that people can be assigned to
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT,
    name TEXT NOT NULL,
    group_type TEXT NOT NULL, -- 'role', 'initiative', 'team'
    requirements TEXT[], -- Skills/interests needed (e.g., ['music', 'leadership'])
    capacity INTEGER, -- Max members (e.g., sunday_count for roles)
    current_count INTEGER DEFAULT 0, -- How many assigned currently
    goal NUMERIC, -- For initiatives: giving goal
    start_date TIMESTAMP,
    leader_id UUID REFERENCES people(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. ASSIGNMENTS TABLE
-- Links people to groups or people to people (volunteer→role, mentee→mentor)
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES people(id), -- The person being assigned
    target_id UUID NOT NULL, -- Group or person they're assigned to
    target_type TEXT NOT NULL, -- 'group' or 'person'
    assignment_type TEXT NOT NULL, -- 'volunteer_to_role', 'mentee_to_mentor', etc.
    match_score NUMERIC, -- Algorithm confidence (0.0-1.0)
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'active', 'completed', 'cancelled'
    workflow_run_id UUID, -- References workflow_runs(id), added later
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. MESSAGES TABLE
-- Notification queue and delivery log
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL REFERENCES people(id),
    channel TEXT NOT NULL, -- 'sms', 'email'
    template TEXT, -- Template name used
    content TEXT NOT NULL, -- Final rendered message
    status TEXT NOT NULL DEFAULT 'queued', -- 'queued', 'sent', 'failed'
    sent_at TIMESTAMP,
    workflow_run_id UUID, -- References workflow_runs(id), added later
    metadata JSONB, -- Delivery details, provider response
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. GIFTS TABLE
-- Financial tracking for giving analysis
CREATE TABLE gifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id UUID NOT NULL REFERENCES people(id),
    initiative_id UUID REFERENCES groups(id), -- Can be NULL for general giving
    amount NUMERIC NOT NULL,
    gift_date TIMESTAMP NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. WORKFLOW_RUNS TABLE
-- Tracks each workflow execution
CREATE TABLE workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_type TEXT NOT NULL, -- 'matching', 'monitoring', 'analysis'
    status TEXT NOT NULL DEFAULT 'classifying', -- 'classifying', 'extracting_params', 'executing', 'awaiting_approval', 'completed', 'failed'
    request_text TEXT NOT NULL, -- Original natural language request
    extracted_params JSONB, -- AI-extracted parameters
    results JSONB, -- Execution results/metrics
    user_id TEXT, -- Who initiated the workflow
    error TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. APPROVAL_GATES TABLE
-- Human oversight checkpoints
CREATE TABLE approval_gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_run_id UUID NOT NULL UNIQUE REFERENCES workflow_runs(id),
    gate_type TEXT NOT NULL, -- 'assignments', 'notifications', 'analysis'
    preview_data JSONB NOT NULL, -- What will change (table diffs, message previews)
    metrics JSONB, -- Coverage %, costs, counts
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    approved_by TEXT,
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. AUDIT_LOG TABLE
-- Complete trace of all function calls
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    workflow_run_id UUID REFERENCES workflow_runs(id),
    function_name TEXT NOT NULL, -- 'load_data', 'match', 'filter', 'send_notification', 'calculate_metrics'
    params JSONB NOT NULL, -- Function parameters
    result JSONB, -- Function output
    user_id TEXT,
    duration_ms INTEGER,
    error TEXT
);

-- Add foreign key constraints for workflow_run_id in assignments and messages
ALTER TABLE assignments ADD CONSTRAINT fk_assignments_workflow 
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id);

ALTER TABLE messages ADD CONSTRAINT fk_messages_workflow 
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id);

-- INDEXES for query performance
-- People indexes
CREATE INDEX idx_people_type ON people(person_type);
CREATE INDEX idx_people_email ON people(email);
CREATE INDEX idx_people_phone ON people(phone);
CREATE INDEX idx_people_visit_date ON people(visit_date) WHERE visit_date IS NOT NULL;

-- Groups indexes
CREATE INDEX idx_groups_type ON groups(group_type);
CREATE INDEX idx_groups_name ON groups(name);

-- Assignments indexes
CREATE INDEX idx_assignments_source ON assignments(source_id);
CREATE INDEX idx_assignments_target ON assignments(target_id);
CREATE INDEX idx_assignments_workflow ON assignments(workflow_run_id);
CREATE INDEX idx_assignments_status ON assignments(status);

-- Messages indexes
CREATE INDEX idx_messages_recipient ON messages(recipient_id);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_workflow ON messages(workflow_run_id);

-- Gifts indexes
CREATE INDEX idx_gifts_donor ON gifts(donor_id);
CREATE INDEX idx_gifts_initiative ON gifts(initiative_id);
CREATE INDEX idx_gifts_date ON gifts(gift_date);

-- Workflow_runs indexes
CREATE INDEX idx_workflow_status ON workflow_runs(status);
CREATE INDEX idx_workflow_template ON workflow_runs(template_type);
CREATE INDEX idx_workflow_created ON workflow_runs(created_at);

-- Approval_gates indexes
CREATE INDEX idx_approval_workflow ON approval_gates(workflow_run_id);
CREATE INDEX idx_approval_status ON approval_gates(status);

-- Audit_log indexes
CREATE INDEX idx_audit_workflow ON audit_log(workflow_run_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_function ON audit_log(function_name);

-- TRIGGERS for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_people_updated_at BEFORE UPDATE ON people
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assignments_updated_at BEFORE UPDATE ON assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

