"""
Streaming version of orchestration with SSE event emission
Uses LangGraph's .astream() to emit events as nodes complete
"""

from typing import Dict, Any, AsyncIterator
from asyncio import Queue
import json

from .graph import create_orchestrator_graph
from .schemas import TemplateType


async def run_orchestration_with_events(
    request: str,
    available_files: list,
    event_queue: Queue
) -> Dict[str, Any]:
    """
    Run orchestration and emit events in REAL-TIME as debate progresses.
    
    Uses LangGraph's .astream() to get node outputs as they complete.
    """
    
    # Build initial state
    initial_state = {
        'request': request,
        'available_files': available_files or [],
        'agent_initiated': False,
        'errors': [],
        'clarifications': []
    }
    
    # Get the compiled graph
    graph = create_orchestrator_graph()
    
    # Track state as we stream
    final_result = None
    
    # Stream through the graph execution
    async for output in graph.astream(initial_state):
        # output is a dict like: {"node_name": state_after_node}
        # We get one output per node that completes
        
        for node_name, state in output.items():
            print(f"[SSE] Node completed: {node_name}")
            
            # Emit events based on which node just completed
            if node_name == "classifier":
                # Check if clarification is needed
                clarifications = state.get('clarifications', [])
                confidence = state.get('confidence', 1.0)

                if clarifications and confidence < 0.8:
                    # Emit clarification_needed event - graph will halt here
                    await event_queue.put({
                        'event': 'clarification_needed',
                        'data': {
                            'question': clarifications[0],
                            'confidence': confidence,
                            'reasoning': state.get('classifier_reasoning', ''),
                            'suggestedTemplate': state['template'].value if 'template' in state else None
                        }
                    })
                else:
                    # Normal classification - proceed to debate
                    await event_queue.put({
                        'event': 'classifier_complete',
                        'data': {
                            'template': state['template'].value,
                            'confidence': confidence,
                            'reasoning': state.get('classifier_reasoning', 'Request classified')
                        }
                    })
            
            elif node_name == "initialize_debate":
                await event_queue.put({
                    'event': 'debate_start',
                    'data': {
                        'agents': ['Planner', 'Operations', 'HumanFlourishing']
                    }
                })
            
            elif node_name == "round_1_proposals":
                # Emit each agent's proposal
                debate_state = state['debate_state']
                for agent_name, proposal in debate_state['proposals'].items():
                    await event_queue.put({
                        'event': 'round_1_proposal',
                        'data': {
                            'agent': agent_name,
                            'round': 1,
                            'messageType': 'proposal',
                            'content': proposal
                        }
                    })
            
            elif node_name == "round_2_rebuttals":
                # Emit each agent's rebuttal
                debate_state = state['debate_state']
                for agent_name, rebuttal in debate_state['rebuttals'].items():
                    await event_queue.put({
                        'event': 'round_2_rebuttal',
                        'data': {
                            'agent': agent_name,
                            'round': 2,
                            'messageType': 'rebuttal',
                            'content': rebuttal
                        }
                    })
            
            elif node_name == "round_3_voting":
                # Emit each agent's vote
                debate_state = state['debate_state']
                for agent_name, vote in debate_state['votes'].items():
                    await event_queue.put({
                        'event': 'round_3_vote',
                        'data': {
                            'agent': agent_name,
                            'round': 3,
                            'messageType': 'vote',
                            'content': f"Voted for {vote}"
                        }
                    })
            
            elif node_name == "tally_votes":
                debate_state = state['debate_state']
                await event_queue.put({
                    'event': 'voting_complete',
                    'data': {
                        'winner': debate_state.get('winning_agent'),
                        'voteTally': debate_state.get('vote_tally', {}),
                        'winningStrategy': debate_state.get('winning_strategy', ''),
                        'tieBrokenByModerator': debate_state.get('tie_broken_by_moderator', False)
                    }
                })
            
            elif node_name == "create_approval_gate":
                await event_queue.put({
                    'event': 'preview_ready',
                    'data': {
                        'approvalId': state['approval_id'],
                        'workflowId': state['workflow_id'],
                        'preview': state['preview'],
                        'template': state['template'].value
                    }
                })
                
                # Save final result
                final_result = state
    
    return final_result