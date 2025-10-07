"""
Multi-Agent Debate Module
Enables 3 agents to debate strategies in parallel
"""

from pathlib import Path
from typing import List
from ...schemas import AgentConfig

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PERSONAS_DIR = PROJECT_ROOT / "prompts" / "agent_personas"

# Agent configurations - centralized for easy modification
AGENT_CONFIGS: List[AgentConfig] = [
    AgentConfig(
        name="Planner",
        persona_file="planner.txt",
        emoji="📊",
        role_description="Strategic thinking, efficiency, scalability"
    ),
    AgentConfig(
        name="Operations",
        persona_file="operations.txt",
        emoji="⚙️",
        role_description="Feasibility, logistics, execution"
    ),
    AgentConfig(
        name="HumanFlourishing",
        persona_file="human_flourishing.txt",
        emoji="🌱",
        role_description="Relationships, wellbeing, human-centered approach"
    )
]


def get_agent_configs() -> List[AgentConfig]:
    """Get list of all agent configurations"""
    return AGENT_CONFIGS


def load_persona(persona_file: str) -> str:
    """Load agent persona prompt from file"""
    persona_path = PERSONAS_DIR / persona_file
    if not persona_path.exists():
        raise FileNotFoundError(f"Persona file not found: {persona_path}")
    return persona_path.read_text()


def get_agent_by_name(name: str) -> AgentConfig:
    """Get agent config by name"""
    for agent in AGENT_CONFIGS:
        if agent.name == name:
            return agent
    raise ValueError(f"Agent '{name}' not found in AGENT_CONFIGS")


# Export key functions for external use
__all__ = [
    'AGENT_CONFIGS',
    'get_agent_configs',
    'load_persona',
    'get_agent_by_name',
]