-- Trellis MVP Seed Data
-- Realistic test data for all 4 use cases

-- Clear existing data (for development resets)
TRUNCATE TABLE audit_log, approval_gates, messages, assignments, gifts, workflow_runs, groups, people RESTART IDENTITY CASCADE;

-- ============================================
-- USE CASE 1: VOLUNTEER MATCHING
-- ============================================

-- Insert 50 volunteers with realistic data
INSERT INTO people (external_id, name, email, phone, person_type, interests, availability_days, metadata) VALUES
('V001', 'John Smith', 'john.smith@email.com', '555-0101', 'volunteer', ARRAY['youth', 'teaching'], ARRAY['Sun', 'Wed'], '{"years_experience": 3}'),
('V002', 'Sarah Johnson', 'sarah.j@email.com', '555-0102', 'volunteer', ARRAY['music', 'worship'], ARRAY['Sun'], '{"instrument": "guitar"}'),
('V003', 'Michael Brown', 'mbrown@email.com', '555-0103', 'volunteer', ARRAY['hospitality', 'greeting'], ARRAY['Sun', 'Tue'], '{}'),
('V004', 'Emily Davis', 'emily.d@email.com', '555-0104', 'volunteer', ARRAY['youth', 'mentoring'], ARRAY['Sun', 'Thu'], '{}'),
('V005', 'David Wilson', 'dwilson@email.com', '555-0105', 'volunteer', ARRAY['tech', 'media'], ARRAY['Sun'], '{"skills": "video editing"}'),
('V006', 'Lisa Anderson', 'l.anderson@email.com', '555-0106', 'volunteer', ARRAY['children', 'teaching'], ARRAY['Sun', 'Sat'], '{}'),
('V007', 'James Martinez', 'jmartinez@email.com', '555-0107', 'volunteer', ARRAY['hospitality', 'cooking'], ARRAY['Sun', 'Wed'], '{}'),
('V008', 'Jennifer Taylor', 'jtaylor@email.com', '555-0108', 'volunteer', ARRAY['worship', 'singing'], ARRAY['Sun'], '{}'),
('V009', 'Robert Garcia', 'rgarcia@email.com', '555-0109', 'volunteer', ARRAY['youth', 'sports'], ARRAY['Sun', 'Sat'], '{}'),
('V010', 'Linda Rodriguez', 'lrodriguez@email.com', '555-0110', 'volunteer', ARRAY['admin', 'organization'], ARRAY['Sun', 'Mon', 'Wed'], '{}'),
('V011', 'William Lee', 'wlee@email.com', '555-0111', 'volunteer', ARRAY['teaching', 'biblical_study'], ARRAY['Sun', 'Thu'], '{}'),
('V012', 'Mary White', 'mwhite@email.com', '555-0112', 'volunteer', ARRAY['children', 'crafts'], ARRAY['Sun'], '{}'),
('V013', 'Christopher Harris', 'charris@email.com', '555-0113', 'volunteer', ARRAY['tech', 'sound'], ARRAY['Sun'], '{}'),
('V014', 'Patricia Clark', 'pclark@email.com', '555-0114', 'volunteer', ARRAY['hospitality', 'greeting'], ARRAY['Sun'], '{}'),
('V015', 'Daniel Lewis', 'dlewis@email.com', '555-0115', 'volunteer', ARRAY['youth', 'games'], ARRAY['Sun', 'Fri'], '{}'),
('V016', 'Barbara Walker', 'bwalker@email.com', '555-0116', 'volunteer', ARRAY['prayer', 'counseling'], ARRAY['Sun', 'Tue'], '{}'),
('V017', 'Thomas Hall', 'thall@email.com', '555-0117', 'volunteer', ARRAY['music', 'drums'], ARRAY['Sun'], '{}'),
('V018', 'Jessica Allen', 'jallen@email.com', '555-0118', 'volunteer', ARRAY['children', 'storytelling'], ARRAY['Sun', 'Wed'], '{}'),
('V019', 'Matthew Young', 'myoung@email.com', '555-0119', 'volunteer', ARRAY['media', 'photography'], ARRAY['Sun'], '{}'),
('V020', 'Karen King', 'kking@email.com', '555-0120', 'volunteer', ARRAY['hospitality', 'decoration'], ARRAY['Sun', 'Sat'], '{}'),
('V021', 'Mark Wright', 'mwright@email.com', '555-0121', 'volunteer', ARRAY['youth', 'mentoring'], ARRAY['Sun', 'Thu'], '{}'),
('V022', 'Nancy Scott', 'nscott@email.com', '555-0122', 'volunteer', ARRAY['worship', 'keyboard'], ARRAY['Sun'], '{}'),
('V023', 'Steven Green', 'sgreen@email.com', '555-0123', 'volunteer', ARRAY['parking', 'safety'], ARRAY['Sun'], '{}'),
('V024', 'Betty Adams', 'badams@email.com', '555-0124', 'volunteer', ARRAY['children', 'teaching'], ARRAY['Sun'], '{}'),
('V025', 'Paul Baker', 'pbaker@email.com', '555-0125', 'volunteer', ARRAY['tech', 'lights'], ARRAY['Sun'], '{}'),
('V026', 'Sandra Gonzalez', 'sgonzalez@email.com', '555-0126', 'volunteer', ARRAY['hospitality', 'info_desk'], ARRAY['Sun'], '{}'),
('V027', 'Andrew Nelson', 'anelson@email.com', '555-0127', 'volunteer', ARRAY['youth', 'teaching'], ARRAY['Sun', 'Wed'], '{}'),
('V028', 'Donna Carter', 'dcarter@email.com', '555-0128', 'volunteer', ARRAY['prayer', 'intercession'], ARRAY['Sun', 'Tue', 'Thu'], '{}'),
('V029', 'Joshua Mitchell', 'jmitchell@email.com', '555-0129', 'volunteer', ARRAY['worship', 'bass'], ARRAY['Sun'], '{}'),
('V030', 'Carol Perez', 'cperez@email.com', '555-0130', 'volunteer', ARRAY['children', 'games'], ARRAY['Sun', 'Sat'], '{}'),
('V031', 'Kenneth Roberts', 'kroberts@email.com', '555-0131', 'volunteer', ARRAY['hospitality', 'greeting'], ARRAY['Sun'], '{}'),
('V032', 'Michelle Turner', 'mturner@email.com', '555-0132', 'volunteer', ARRAY['admin', 'database'], ARRAY['Sun', 'Mon'], '{}'),
('V033', 'Kevin Phillips', 'kphillips@email.com', '555-0133', 'volunteer', ARRAY['youth', 'sports'], ARRAY['Sun', 'Sat'], '{}'),
('V034', 'Dorothy Campbell', 'dcampbell@email.com', '555-0134', 'volunteer', ARRAY['teaching', 'women'], ARRAY['Sun', 'Wed'], '{}'),
('V035', 'Brian Parker', 'bparker@email.com', '555-0135', 'volunteer', ARRAY['tech', 'computers'], ARRAY['Sun'], '{}'),
('V036', 'Kimberly Evans', 'kevans@email.com', '555-0136', 'volunteer', ARRAY['children', 'safety'], ARRAY['Sun'], '{}'),
('V037', 'George Edwards', 'gedwards@email.com', '555-0137', 'volunteer', ARRAY['hospitality', 'setup'], ARRAY['Sun'], '{}'),
('V038', 'Helen Collins', 'hcollins@email.com', '555-0138', 'volunteer', ARRAY['worship', 'singing'], ARRAY['Sun'], '{}'),
('V039', 'Edward Stewart', 'estewart@email.com', '555-0139', 'volunteer', ARRAY['parking', 'traffic'], ARRAY['Sun'], '{}'),
('V040', 'Deborah Sanchez', 'dsanchez@email.com', '555-0140', 'volunteer', ARRAY['prayer', 'healing'], ARRAY['Sun', 'Tue'], '{}'),
('V041', 'Jason Morris', 'jmorris@email.com', '555-0141', 'volunteer', ARRAY['youth', 'leadership'], ARRAY['Sun', 'Wed'], '{}'),
('V042', 'Shirley Rogers', 'srogers@email.com', '555-0142', 'volunteer', ARRAY['hospitality', 'food'], ARRAY['Sun'], '{}'),
('V043', 'Ryan Reed', 'rreed@email.com', '555-0143', 'volunteer', ARRAY['media', 'slides'], ARRAY['Sun'], '{}'),
('V044', 'Angela Cook', 'acook@email.com', '555-0144', 'volunteer', ARRAY['children', 'nursery'], ARRAY['Sun'], '{}'),
('V045', 'Justin Morgan', 'jmorgan@email.com', '555-0145', 'volunteer', ARRAY['tech', 'streaming'], ARRAY['Sun'], '{}'),
('V046', 'Melissa Bell', 'mbell@email.com', '555-0146', 'volunteer', ARRAY['worship', 'vocals'], ARRAY['Sun'], '{}'),
('V047', 'Gary Murphy', 'gmurphy@email.com', '555-0147', 'volunteer', ARRAY['hospitality', 'greeting'], ARRAY['Sun'], '{}'),
('V048', 'Stephanie Bailey', 'sbailey@email.com', '555-0148', 'volunteer', ARRAY['children', 'teaching'], ARRAY['Sun', 'Wed'], '{}'),
('V049', 'Jacob Rivera', 'jrivera@email.com', '555-0149', 'volunteer', ARRAY['youth', 'mentoring'], ARRAY['Sun', 'Thu'], '{}'),
('V050', 'Virginia Cooper', 'vcooper@email.com', '555-0150', 'volunteer', ARRAY['admin', 'communication'], ARRAY['Sun', 'Mon', 'Fri'], '{}');

-- Insert 10 roles (groups) that need volunteers
INSERT INTO groups (external_id, name, group_type, requirements, capacity, current_count, metadata) VALUES
('R001', 'Youth Leader', 'role', ARRAY['youth', 'mentoring'], 5, 0, '{"age_group": "teens", "time": "10:30am"}'),
('R002', 'Worship Team', 'role', ARRAY['music', 'worship'], 8, 0, '{"rehearsal": "Saturday 6pm"}'),
('R003', 'Greeter', 'role', ARRAY['hospitality', 'greeting'], 6, 0, '{"arrive_early": true}'),
('R004', 'Children''s Ministry', 'role', ARRAY['children', 'teaching'], 10, 0, '{"age_group": "5-12"}'),
('R005', 'Tech Team', 'role', ARRAY['tech', 'media'], 4, 0, '{"training_required": true}'),
('R006', 'Prayer Team', 'role', ARRAY['prayer', 'counseling'], 4, 0, '{"after_service": true}'),
('R007', 'Hospitality Team', 'role', ARRAY['hospitality', 'food'], 8, 0, '{"setup_cleanup": true}'),
('R008', 'Parking Team', 'role', ARRAY['parking', 'safety'], 3, 0, '{"outdoor": true}'),
('R009', 'Admin Support', 'role', ARRAY['admin', 'organization'], 3, 0, '{"weekday_hours": true}'),
('R010', 'Small Group Leader', 'role', ARRAY['teaching', 'leadership'], 6, 0, '{"weekly_commitment": true}');

-- ============================================
-- USE CASE 2: VISITOR MONITORING
-- ============================================

-- Insert 30 visitors spanning 60 days
INSERT INTO people (external_id, name, email, phone, person_type, visit_date, last_contact_date, metadata) VALUES
-- Recent visitors (< 14 days) - should NOT be flagged
('VIS001', 'Alice Thompson', 'alice.t@email.com', '555-0201', 'visitor', NOW() - INTERVAL '5 days', NOW() - INTERVAL '3 days', '{"first_visit": true}'),
('VIS002', 'Bob Martinez', 'bob.m@email.com', '555-0202', 'visitor', NOW() - INTERVAL '8 days', NOW() - INTERVAL '6 days', '{"first_visit": true}'),
('VIS003', 'Charlie Davis', 'charlie.d@email.com', '555-0203', 'visitor', NOW() - INTERVAL '10 days', NULL, '{"first_visit": true}'),
('VIS004', 'Diana Wilson', 'diana.w@email.com', '555-0204', 'visitor', NOW() - INTERVAL '12 days', NOW() - INTERVAL '11 days', '{"first_visit": true}'),

-- Visitors 14-30 days ago, NOT contacted - SHOULD be flagged
('VIS005', 'Ethan Brown', 'ethan.b@email.com', '555-0205', 'visitor', NOW() - INTERVAL '15 days', NULL, '{"first_visit": true, "interests": "youth ministry"}'),
('VIS006', 'Fiona Garcia', 'fiona.g@email.com', '555-0206', 'visitor', NOW() - INTERVAL '18 days', NULL, '{"first_visit": true}'),
('VIS007', 'George Taylor', 'george.t@email.com', '555-0207', 'visitor', NOW() - INTERVAL '21 days', NULL, '{"first_visit": true, "family_size": 4}'),
('VIS008', 'Hannah Lee', 'hannah.l@email.com', '555-0208', 'visitor', NOW() - INTERVAL '24 days', NULL, '{"first_visit": true}'),
('VIS009', 'Ian White', 'ian.w@email.com', '555-0209', 'visitor', NOW() - INTERVAL '27 days', NULL, '{"first_visit": true}'),

-- Visitors 14-30 days ago, already contacted - should NOT be flagged
('VIS010', 'Julia Harris', 'julia.h@email.com', '555-0210', 'visitor', NOW() - INTERVAL '16 days', NOW() - INTERVAL '14 days', '{"first_visit": true}'),
('VIS011', 'Kevin Clark', 'kevin.c@email.com', '555-0211', 'visitor', NOW() - INTERVAL '20 days', NOW() - INTERVAL '18 days', '{"first_visit": true}'),
('VIS012', 'Laura Lewis', 'laura.l@email.com', '555-0212', 'visitor', NOW() - INTERVAL '25 days', NOW() - INTERVAL '23 days', '{"first_visit": true}'),

-- Visitors 30+ days ago, NOT contacted - SHOULD be flagged (high priority)
('VIS013', 'Michael Walker', 'michael.w@email.com', '555-0213', 'visitor', NOW() - INTERVAL '35 days', NULL, '{"first_visit": true, "referred_by": "friend"}'),
('VIS014', 'Nina Hall', 'nina.h@email.com', '555-0214', 'visitor', NOW() - INTERVAL '40 days', NULL, '{"first_visit": true}'),
('VIS015', 'Oliver Young', 'oliver.y@email.com', '555-0215', 'visitor', NOW() - INTERVAL '45 days', NULL, '{"first_visit": true, "interests": "small groups"}'),
('VIS016', 'Paula King', 'paula.k@email.com', '555-0216', 'visitor', NOW() - INTERVAL '50 days', NULL, '{"first_visit": true}'),

-- Visitors 30+ days ago, contacted - should NOT be flagged
('VIS017', 'Quinn Wright', 'quinn.w@email.com', '555-0217', 'visitor', NOW() - INTERVAL '32 days', NOW() - INTERVAL '30 days', '{"first_visit": true}'),
('VIS018', 'Rachel Scott', 'rachel.s@email.com', '555-0218', 'visitor', NOW() - INTERVAL '38 days', NOW() - INTERVAL '35 days', '{"first_visit": true}'),
('VIS019', 'Sam Green', 'sam.g@email.com', '555-0219', 'visitor', NOW() - INTERVAL '42 days', NOW() - INTERVAL '40 days', '{"first_visit": true}'),
('VIS020', 'Tina Adams', 'tina.a@email.com', '555-0220', 'visitor', NOW() - INTERVAL '48 days', NOW() - INTERVAL '46 days', '{"first_visit": true}'),

-- Mix of older visitors
('VIS021', 'Uma Baker', 'uma.b@email.com', '555-0221', 'visitor', NOW() - INTERVAL '55 days', NULL, '{"first_visit": true}'),
('VIS022', 'Victor Nelson', 'victor.n@email.com', '555-0222', 'visitor', NOW() - INTERVAL '58 days', NOW() - INTERVAL '56 days', '{"first_visit": true}'),
('VIS023', 'Wendy Carter', 'wendy.c@email.com', '555-0223', 'visitor', NOW() - INTERVAL '19 days', NULL, '{"first_visit": true}'),
('VIS024', 'Xavier Mitchell', 'xavier.m@email.com', '555-0224', 'visitor', NOW() - INTERVAL '22 days', NULL, '{"first_visit": true}'),
('VIS025', 'Yara Perez', 'yara.p@email.com', '555-0225', 'visitor', NOW() - INTERVAL '28 days', NULL, '{"first_visit": true}'),
('VIS026', 'Zack Roberts', 'zack.r@email.com', '555-0226', 'visitor', NOW() - INTERVAL '31 days', NOW() - INTERVAL '29 days', '{"first_visit": true}'),
('VIS027', 'Amy Turner', 'amy.t@email.com', '555-0227', 'visitor', NOW() - INTERVAL '36 days', NULL, '{"first_visit": true}'),
('VIS028', 'Ben Phillips', 'ben.p@email.com', '555-0228', 'visitor', NOW() - INTERVAL '44 days', NULL, '{"first_visit": true}'),
('VIS029', 'Cara Campbell', 'cara.c@email.com', '555-0229', 'visitor', NOW() - INTERVAL '52 days', NOW() - INTERVAL '50 days', '{"first_visit": true}'),
('VIS030', 'Dan Parker', 'dan.p@email.com', '555-0230', 'visitor', NOW() - INTERVAL '60 days', NULL, '{"first_visit": true}');

-- ============================================
-- USE CASE 3: GIVING ANALYSIS
-- ============================================

-- Insert 5 initiatives
INSERT INTO groups (external_id, name, group_type, goal, start_date, metadata) VALUES
('INIT001', 'Building Fund', 'initiative', 50000.00, NOW() - INTERVAL '90 days', '{"purpose": "New sanctuary"}'),
('INIT002', 'Mission Trip', 'initiative', 15000.00, NOW() - INTERVAL '60 days', '{"destination": "Haiti"}'),
('INIT003', 'Youth Camp', 'initiative', 8000.00, NOW() - INTERVAL '45 days', '{"dates": "July 15-20"}'),
('INIT004', 'Community Outreach', 'initiative', 12000.00, NOW() - INTERVAL '75 days', '{"programs": "food bank, tutoring"}'),
('INIT005', 'General Fund', 'initiative', 100000.00, NOW() - INTERVAL '365 days', '{"annual": true}');

-- Insert donor people (some will be regular, some lapsed)
INSERT INTO people (external_id, name, email, phone, person_type, metadata) VALUES
('D001', 'Donor Alice', 'alice.donor@email.com', '555-0301', 'donor', '{}'),
('D002', 'Donor Bob', 'bob.donor@email.com', '555-0302', 'donor', '{}'),
('D003', 'Donor Carol', 'carol.donor@email.com', '555-0303', 'donor', '{}'),
('D004', 'Donor David', 'david.donor@email.com', '555-0304', 'donor', '{}'),
('D005', 'Donor Eve', 'eve.donor@email.com', '555-0305', 'donor', '{}'),
('D006', 'Donor Frank', 'frank.donor@email.com', '555-0306', 'donor', '{}'),
('D007', 'Donor Grace', 'grace.donor@email.com', '555-0307', 'donor', '{}'),
('D008', 'Donor Henry', 'henry.donor@email.com', '555-0308', 'donor', '{}'),
('D009', 'Donor Iris', 'iris.donor@email.com', '555-0309', 'donor', '{}'),
('D010', 'Donor Jack', 'jack.donor@email.com', '555-0310', 'donor', '{}'),
('D011', 'Donor Karen', 'karen.donor@email.com', '555-0311', 'donor', '{}'),
('D012', 'Donor Larry', 'larry.donor@email.com', '555-0312', 'donor', '{}'),
('D013', 'Donor Monica', 'monica.donor@email.com', '555-0313', 'donor', '{}'),
('D014', 'Donor Nathan', 'nathan.donor@email.com', '555-0314', 'donor', '{}'),
('D015', 'Donor Olivia', 'olivia.donor@email.com', '555-0315', 'donor', '{}');

-- Insert 200 gift records
-- Get donor and initiative IDs for reference
DO $$
DECLARE
    donor_ids UUID[];
    init_ids UUID[];
    i INTEGER;
    random_donor UUID;
    random_init UUID;
    random_amount NUMERIC;
    random_days INTEGER;
BEGIN
    -- Get all donor IDs
    SELECT ARRAY_AGG(id) INTO donor_ids FROM people WHERE person_type = 'donor';
    SELECT ARRAY_AGG(id) INTO init_ids FROM groups WHERE group_type = 'initiative';
    
    -- Create 200 gifts with varying patterns
    FOR i IN 1..200 LOOP
        -- Random donor
        random_donor := donor_ids[1 + floor(random() * array_length(donor_ids, 1))];
        -- Random initiative
        random_init := init_ids[1 + floor(random() * array_length(init_ids, 1))];
        -- Random amount between $20 and $500
        random_amount := 20 + floor(random() * 480);
        -- Random date within last 120 days
        random_days := floor(random() * 120);
        
        INSERT INTO gifts (donor_id, initiative_id, amount, gift_date)
        VALUES (random_donor, random_init, random_amount, NOW() - (random_days || ' days')::INTERVAL);
    END LOOP;
    
    -- Add some lapsed donors (last gift > 90 days ago)
    -- Donors D011-D015 will only have old gifts
    DELETE FROM gifts WHERE donor_id IN (
        SELECT id FROM people WHERE external_id IN ('D011', 'D012', 'D013', 'D014', 'D015')
    );
    
    -- Add old gifts for lapsed donors (3 gifts each)
    INSERT INTO gifts (donor_id, initiative_id, amount, gift_date)
    SELECT 
        p.id,
        init_ids[1 + floor(random() * array_length(init_ids, 1))],
        50 + floor(random() * 200),
        NOW() - ((95 + floor(random() * 100)) || ' days')::INTERVAL
    FROM people p
    CROSS JOIN generate_series(1, 3) AS gs
    WHERE p.external_id IN ('D011', 'D012', 'D013', 'D014', 'D015');
END $$;

-- ============================================
-- USE CASE 4: MENTOR MATCHING
-- ============================================

-- Insert 12 mentors with capacity
INSERT INTO people (external_id, name, email, phone, person_type, interests, capacity, metadata) VALUES
('M001', 'Mentor Sarah', 'mentor.sarah@email.com', '555-0401', 'mentor', ARRAY['career', 'faith'], 2, '{"experience_years": 5}'),
('M002', 'Mentor John', 'mentor.john@email.com', '555-0402', 'mentor', ARRAY['relationships', 'faith'], 3, '{"experience_years": 7}'),
('M003', 'Mentor Lisa', 'mentor.lisa@email.com', '555-0403', 'mentor', ARRAY['career', 'leadership'], 2, '{"experience_years": 4}'),
('M004', 'Mentor Mark', 'mentor.mark@email.com', '555-0404', 'mentor', ARRAY['faith', 'biblical_study'], 2, '{"experience_years": 10}'),
('M005', 'Mentor Emma', 'mentor.emma@email.com', '555-0405', 'mentor', ARRAY['relationships', 'recovery'], 1, '{"experience_years": 3}'),
('M006', 'Mentor Chris', 'mentor.chris@email.com', '555-0406', 'mentor', ARRAY['career', 'business'], 3, '{"experience_years": 8}'),
('M007', 'Mentor Rachel', 'mentor.rachel@email.com', '555-0407', 'mentor', ARRAY['faith', 'women'], 2, '{"experience_years": 6}'),
('M008', 'Mentor Tom', 'mentor.tom@email.com', '555-0408', 'mentor', ARRAY['leadership', 'men'], 2, '{"experience_years": 9}'),
('M009', 'Mentor Anna', 'mentor.anna@email.com', '555-0409', 'mentor', ARRAY['relationships', 'parenting'], 1, '{"experience_years": 5}'),
('M010', 'Mentor Steve', 'mentor.steve@email.com', '555-0410', 'mentor', ARRAY['career', 'tech'], 2, '{"experience_years": 4}'),
('M011', 'Mentor Maria', 'mentor.maria@email.com', '555-0411', 'mentor', ARRAY['faith', 'bilingual'], 2, '{"experience_years": 7}'),
('M012', 'Mentor Paul', 'mentor.paul@email.com', '555-0412', 'mentor', ARRAY['leadership', 'biblical_study'], 3, '{"experience_years": 12}');

-- Insert 18 mentees seeking mentors
INSERT INTO people (external_id, name, email, phone, person_type, interests, metadata) VALUES
('ME001', 'Mentee Alex', 'mentee.alex@email.com', '555-0501', 'mentee', ARRAY['career', 'faith'], '{"age": 22, "new_believer": true}'),
('ME002', 'Mentee Bella', 'mentee.bella@email.com', '555-0502', 'mentee', ARRAY['relationships', 'faith'], '{"age": 25}'),
('ME003', 'Mentee Carlos', 'mentee.carlos@email.com', '555-0503', 'mentee', ARRAY['career', 'leadership'], '{"age": 28}'),
('ME004', 'Mentee Dana', 'mentee.dana@email.com', '555-0504', 'mentee', ARRAY['faith', 'biblical_study'], '{"age": 30}'),
('ME005', 'Mentee Eli', 'mentee.eli@email.com', '555-0505', 'mentee', ARRAY['relationships', 'recovery'], '{"age": 35}'),
('ME006', 'Mentee Fay', 'mentee.fay@email.com', '555-0506', 'mentee', ARRAY['career', 'business'], '{"age": 26}'),
('ME007', 'Mentee Gina', 'mentee.gina@email.com', '555-0507', 'mentee', ARRAY['faith', 'women'], '{"age": 24}'),
('ME008', 'Mentee Hank', 'mentee.hank@email.com', '555-0508', 'mentee', ARRAY['leadership', 'men'], '{"age": 29}'),
('ME009', 'Mentee Ivy', 'mentee.ivy@email.com', '555-0509', 'mentee', ARRAY['relationships', 'parenting'], '{"age": 32}'),
('ME010', 'Mentee Jake', 'mentee.jake@email.com', '555-0510', 'mentee', ARRAY['career', 'tech'], '{"age": 23}'),
('ME011', 'Mentee Kim', 'mentee.kim@email.com', '555-0511', 'mentee', ARRAY['faith', 'bilingual'], '{"age": 27}'),
('ME012', 'Mentee Leo', 'mentee.leo@email.com', '555-0512', 'mentee', ARRAY['leadership', 'biblical_study'], '{"age": 31}'),
('ME013', 'Mentee Mia', 'mentee.mia@email.com', '555-0513', 'mentee', ARRAY['career', 'faith'], '{"age": 21}'),
('ME014', 'Mentee Noah', 'mentee.noah@email.com', '555-0514', 'mentee', ARRAY['relationships', 'faith'], '{"age": 24}'),
('ME015', 'Mentee Ola', 'mentee.ola@email.com', '555-0515', 'mentee', ARRAY['career', 'leadership'], '{"age": 26}'),
('ME016', 'Mentee Pete', 'mentee.pete@email.com', '555-0516', 'mentee', ARRAY['faith', 'biblical_study'], '{"age": 28}'),
('ME017', 'Mentee Quinn', 'mentee.quinn@email.com', '555-0517', 'mentee', ARRAY['relationships', 'recovery'], '{"age": 33}'),
('ME018', 'Mentee Rita', 'mentee.rita@email.com', '555-0518', 'mentee', ARRAY['career', 'business'], '{"age": 25}');

-- Summary of seeded data:
-- ✓ 50 volunteers with diverse interests and availability
-- ✓ 10 roles needing volunteers
-- ✓ 30 visitors (about 10 should be flagged for follow-up based on 14-day rule)
-- ✓ 5 initiatives with goals
-- ✓ 15 donors with 200 gifts (5 donors are lapsed >90 days)
-- ✓ 12 mentors with total capacity of ~24
-- ✓ 18 mentees seeking mentors

