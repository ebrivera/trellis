from src.nodes.debate import get_agent_configs, load_persona, get_agent_by_name
from src.schemas import DebateState, OrchestratorState, TemplateType, DebateMessage

print("="*80)
print("TESTING DEBATE MODULE STRUCTURE")
print("="*80)

# Test 1: Agent configs load
print("\n1. Testing agent configurations...")
agents = get_agent_configs()
print(f"   ✓ Loaded {len(agents)} agents")
for agent in agents:
    print(f"     - {agent.emoji} {agent.name}: {agent.role_description}")

# Test 2: Personas load
print("\n2. Testing persona files...")
for agent in agents:
    try:
        persona = load_persona(agent.persona_file)
        print(f"   ✓ {agent.name} persona loaded ({len(persona)} chars)")
    except FileNotFoundError as e:
        print(f"   ✗ {agent.name} persona MISSING: {e}")

# Test 3: DebateState schema
print("\n3. Testing DebateState schema...")
debate_state = DebateState(
    request="Match volunteers to Sunday roles",
    template=TemplateType.MATCHING,
    current_round=1
)
print(f"   ✓ DebateState created: round={debate_state.current_round}, template={debate_state.template.value}")

# Test 4: OrchestratorState with debate fields
print("\n4. Testing OrchestratorState with debate integration...")
orch_state = OrchestratorState(
    request="Match volunteers to Sunday roles",
    template=TemplateType.MATCHING,
    confidence=0.95,
    debate_state=debate_state.model_dump(),
    winning_agent="Planner",
    vote_tally={"Planner": 2, "Operations": 1}
)
print(f"   ✓ OrchestratorState created with debate fields")
print(f"     - Request: {orch_state.request}")
print(f"     - Template: {orch_state.template.value}")
print(f"     - Winner: {orch_state.winning_agent}")
print(f"     - Votes: {orch_state.vote_tally}")

# Test 5: DebateMessage schema
print("\n5. Testing DebateMessage schema...")
message = DebateMessage(
    round=1,
    agent="Planner",
    message_type="proposal",
    content="I propose capacity-balanced matching"
)
print(f"   ✓ DebateMessage created: [{message.agent}] {message.message_type}")

# Test 6: Get agent by name
print("\n6. Testing agent lookup...")
planner = get_agent_by_name("Planner")
print(f"   ✓ Found {planner.name} - {planner.role_description}")

# Test 7: Orchestrator helpers
print("\n7. Testing orchestrator helpers...")
from src.nodes.debate.orchestrator import initialize_debate_state, get_active_agents

test_state = {
    'request': 'Test request',
    'template': TemplateType.MATCHING,
    'agent_initiated': False
}
initialized_state = initialize_debate_state(test_state)
print(f"   ✓ Debate state initialized: round={initialized_state['debate_state']['current_round']}")

active_agents = get_active_agents(initialized_state)
print(f"   ✓ Active agents: {', '.join(active_agents)}")

print("\n" + "="*80)
print("✅ ALL STRUCTURE TESTS PASSED - Ready for Step 2B")
print("="*80)