"""
./orchestrator/src/nodes/debate/voting.py
Voting Node - Tallies votes and determines winner (with tie-breaking)
"""

from typing import Dict, Any
from .tiebreaker import check_for_tie, moderator_breaks_tie


def tally_votes_and_determine_winner(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Count votes and determine debate winner.

    VETO OVERRIDE: If HumanFlourishing invoked "ABSOLUTE VETO" in their proposal or rebuttal,
    they automatically win regardless of vote counts. This enforces moral/ethical boundaries.

    Args:
        state: Orchestrator state with completed voting

    Returns:
        Updated state with winning_agent, winning_strategy, vote_tally
    """
    debate_state = state['debate_state']

    # Count votes
    vote_counts = {}
    for voted_for in debate_state['votes'].values():
        vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1

    print("\n" + "="*80)
    print("🗳️  VOTE TALLYING")
    print("="*80)
    print(f"Votes cast: {debate_state['votes']}")
    print(f"Vote tally: {vote_counts}")

    # CHECK FOR ABSOLUTE VETO (takes precedence over all votes)
    veto_agent = _check_for_absolute_veto(debate_state)
    if veto_agent:
        print(f"\n🚨 ABSOLUTE VETO DETECTED from {veto_agent}")
        print(f"   Ethical override: {veto_agent} wins automatically")
        print(f"   Vote counts overridden due to moral/ethical veto")

        winning_proposal = debate_state['proposals'][veto_agent]

        # Determine if this is a TOTAL REJECTION or PARTIAL REJECTION
        is_total_rejection = _is_total_rejection(winning_proposal)

        debate_state['winning_agent'] = veto_agent
        debate_state['winning_strategy'] = winning_proposal
        debate_state['vote_tally'] = vote_counts
        debate_state['tie_broken_by_moderator'] = False
        debate_state['veto_override'] = True
        debate_state['veto_type'] = 'total_rejection' if is_total_rejection else 'partial_rejection'

        if is_total_rejection:
            print(f"   🚫 TOTAL REJECTION: Request violates ethical principles")
            print(f"   → Workflow will halt and return clarification to user")
        else:
            print(f"   ✏️  PARTIAL REJECTION: Sanitized alternative proposed")
            print(f"   → Workflow will continue with modified parameters")

        print(f"\n🏆 Winner: {veto_agent} (ABSOLUTE VETO override)")
        print("="*80 + "\n")
        return state

    # Check for tie
    if check_for_tie(debate_state):
        print("\n⚠️  TIE DETECTED - Invoking moderator...")
        state = moderator_breaks_tie(state)
        debate_state = state['debate_state']  # Refresh after moderator update
    else:
        # Normal case: clear winner
        winner_name = max(vote_counts, key=vote_counts.get)
        winning_proposal = debate_state['proposals'][winner_name]

        debate_state['winning_agent'] = winner_name
        debate_state['winning_strategy'] = winning_proposal
        debate_state['vote_tally'] = vote_counts
        debate_state['tie_broken_by_moderator'] = False

        print(f"\n🏆 Winner: {winner_name} ({vote_counts[winner_name]}/{len(debate_state['votes'])} votes)")

    print("="*80 + "\n")

    return state


def _check_for_absolute_veto(debate_state: Dict[str, Any]) -> str:
    """
    Check if any agent (typically HumanFlourishing) invoked an ABSOLUTE VETO.

    Returns:
        Agent name if veto found, None otherwise
    """
    # Check proposals for veto language
    for agent_name, proposal in debate_state.get('proposals', {}).items():
        if proposal and _contains_veto_language(proposal):
            return agent_name

    # Check rebuttals for veto language
    for agent_name, rebuttal in debate_state.get('rebuttals', {}).items():
        if rebuttal and _contains_veto_language(rebuttal):
            return agent_name

    return None


def _contains_veto_language(text: str) -> bool:
    """
    Detect if text contains ABSOLUTE VETO or similar strong ethical override language.

    Checks for explicit "absolute veto" phrases as well as strong ethical rejection language.

    Returns:
        True if veto language detected
    """
    if not text:
        return False

    text_lower = text.lower()

    # Primary veto phrases (strongest signal)
    primary_veto = [
        "absolute veto",
        "invoke absolute veto",
        "i invoke an absolute veto",
        "this is an absolute veto"
    ]

    # Secondary veto indicators (strong ethical objection)
    secondary_veto = [
        "violates core values",
        "contradicts grace",
        "discriminatory",
        "conditional care",
        "exclud" # catches "exclusion", "exclude", "exclusionary"
    ]

    # Must contain primary veto OR multiple secondary indicators
    if any(phrase in text_lower for phrase in primary_veto):
        return True

    # Require at least 2 secondary indicators + strong rejection words
    secondary_count = sum(1 for phrase in secondary_veto if phrase in text_lower)
    has_rejection = any(word in text_lower for word in ["cannot support", "strongly disagree", "violates", "reject"])

    return secondary_count >= 2 and has_rejection


def _is_total_rejection(proposal: str) -> bool:
    """
    Determine if a veto proposal is a TOTAL REJECTION (entire request unethical)
    or a PARTIAL REJECTION (specific filters/aspects need modification).

    Total rejection indicators:
    - Explicitly vetoes "this request" or "the request"
    - Says request "cannot be executed" or "cannot proceed"
    - Pure criticism with no constructive alternative
    - Primarily negative/ethical objection

    Partial rejection indicators:
    - Vetoes specific filters (tithing, giving history, etc.)
    - Proposes modified version of same core action
    - Example: "Match single moms BUT WITHOUT tithing filter"

    Returns:
        True if total rejection, False if partial rejection with alternative
    """
    if not proposal:
        return True  # Empty proposal = total rejection

    text_lower = proposal.lower()

    # PRIORITY CHECK: Explicit rejection of entire request
    # If agent says they're vetoing "this request" or "the request", it's total
    explicit_request_rejection = [
        "veto on this request",
        "veto this request",
        "reject this request",
        "cannot execute this request",
        "this request violates",
        "this request is",
        "the request violates",
        "the entire request"
    ]

    if any(phrase in text_lower for phrase in explicit_request_rejection):
        return True  # Explicitly vetoing the entire request

    # Check for veto of specific filters (partial rejection)
    filter_specific_veto = [
        "veto on the tithing",
        "veto the tithing filter",
        "exclude the tithing",
        "remove the tithing filter",
        "without the tithing",
        "but exclude",
        "except for the filter"
    ]

    if any(phrase in text_lower for phrase in filter_specific_veto):
        return False  # Vetoing a specific filter, not the whole request

    # Check for constructive alternative language
    alternative_phrases = [
        "instead",
        "alternative",
        "recommend",
        "better approach",
        "suggest",
        "propose that we",
        "a more ethical approach",
        "we should"
    ]

    has_alternative = any(phrase in text_lower for phrase in alternative_phrases)

    # If it has alternative language AND doesn't explicitly reject the request,
    # it might be a partial rejection. But we need to be cautious.
    # If the proposal is mostly criticism (>50% negative), it's likely total.
    negative_indicators = [
        "violates",
        "manipulation",
        "transactional",
        "unethical",
        "harmful",
        "damages",
        "contradicts",
        "exploitation"
    ]

    negative_count = sum(1 for phrase in negative_indicators if phrase in text_lower)

    # If heavy criticism (3+ negative indicators), likely a total rejection
    # even if alternatives are mentioned
    if negative_count >= 3:
        return True

    # If alternative language but light criticism, partial rejection
    if has_alternative:
        return False

    # Otherwise, default to total rejection (pure veto with no alternative)
    return True